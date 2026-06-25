from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import CancelledError, Future, ThreadPoolExecutor
from dataclasses import dataclass
from threading import Event, RLock
from typing import Any

from .jsonrpc import (
    INTERNAL_ERROR,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    JsonRpcMessage,
    create_error_response,
    create_response,
)


@dataclass
class CancelToken:
    id: int | str
    _cancel_event: Event | None = None

    def __post_init__(self) -> None:
        if self._cancel_event is None:
            self._cancel_event = Event()

    def cancel(self) -> None:
        self._cancel_event.set()

    def is_canceled(self) -> bool:
        return self._cancel_event.is_set()

    def raise_if_canceled(self) -> None:
        if self.is_canceled():
            raise RequestCancelled


class RequestCancelled(Exception):
    pass


@dataclass(frozen=True)
class _HandlerRegistration:
    handler: Handler
    run_in_worker: bool = False


@dataclass
class _PendingRequest:
    token: CancelToken
    future: Future[Any] | None = None


Handler = Callable[[dict[str, Any] | list[Any] | None, CancelToken], Any]


class MethodDispatcher:
    def __init__(self, *, max_workers: int = 0) -> None:
        self._handlers: dict[str, _HandlerRegistration] = {}
        self._pending: dict[int | str, _PendingRequest] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers) if max_workers > 0 else None
        self._lock = RLock()
        self.register("$/cancelRequest", self._handle_cancel_request)

    def register(self, method: str, handler: Handler, *, run_in_worker: bool = False) -> None:
        self._handlers[method] = _HandlerRegistration(handler, run_in_worker)

    def dispatch(self, message: JsonRpcMessage) -> JsonRpcMessage | None:
        if message.method is None:
            return create_error_response(message.id, INVALID_REQUEST, "Expected request or notification")

        if message.method == "$/cancelRequest":
            self._handle_cancel_request(message.params, CancelToken("$/cancelRequest"))
            return None

        registration = self._handlers.get(message.method)
        if registration is None:
            if message.is_notification:
                return None
            return create_error_response(
                message.id,
                METHOD_NOT_FOUND,
                f"Method not found: {message.method}",
            )

        token = CancelToken(message.id if message.id is not None else "notification")
        if message.is_request:
            with self._lock:
                self._pending[message.id] = _PendingRequest(token=token)

        try:
            result = self._execute(registration, message.params, token, message.id if message.is_request else None)
        except (CancelledError, RequestCancelled):
            return None
        except Exception as exc:
            if message.is_notification:
                return None
            return create_error_response(message.id, INTERNAL_ERROR, "Internal error", str(exc))
        finally:
            if message.is_request:
                with self._lock:
                    self._pending.pop(message.id, None)

        if message.is_notification or token.is_canceled():
            return None

        return create_response(message.id, result)

    def cancel_request(self, id: int | str) -> bool:
        with self._lock:
            pending = self._pending.get(id)
            if pending is None:
                return False
            pending.token.cancel()
            if pending.future is not None:
                pending.future.cancel()
            return True

    def is_canceled(self, id: int | str) -> bool:
        with self._lock:
            pending = self._pending.get(id)
            return pending.token.is_canceled() if pending is not None else False

    def shutdown(self) -> None:
        if self._executor is not None:
            self._executor.shutdown(cancel_futures=True)

    def _execute(
        self,
        registration: _HandlerRegistration,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
        request_id: int | str | None,
    ) -> Any:
        if not registration.run_in_worker or self._executor is None:
            return registration.handler(params, token)

        future = self._executor.submit(registration.handler, params, token)
        if request_id is not None:
            with self._lock:
                pending = self._pending.get(request_id)
                if pending is not None:
                    pending.future = future
        return future.result()

    def _handle_cancel_request(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> None:
        if not isinstance(params, dict) or "id" not in params:
            return None
        id_value = params["id"]
        if isinstance(id_value, (int, str)):
            self.cancel_request(id_value)
        return None
