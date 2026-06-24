from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock
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
    _canceled: bool = False

    def cancel(self) -> None:
        self._canceled = True

    def is_canceled(self) -> bool:
        return self._canceled


Handler = Callable[[dict[str, Any] | list[Any] | None, CancelToken], Any]


class MethodDispatcher:
    def __init__(self) -> None:
        self._handlers: dict[str, Handler] = {}
        self._pending: dict[int | str, CancelToken] = {}
        self._lock = RLock()
        self.register("$/cancelRequest", self._handle_cancel_request)

    def register(self, method: str, handler: Handler) -> None:
        self._handlers[method] = handler

    def dispatch(self, message: JsonRpcMessage) -> JsonRpcMessage | None:
        if message.method is None:
            return create_error_response(message.id, INVALID_REQUEST, "Expected request or notification")

        if message.method == "$/cancelRequest":
            self._handle_cancel_request(message.params, CancelToken("$/cancelRequest"))
            return None

        handler = self._handlers.get(message.method)
        if handler is None:
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
                self._pending[message.id] = token

        try:
            result = handler(message.params, token)
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
            token = self._pending.get(id)
            if token is None:
                return False
            token.cancel()
            return True

    def is_canceled(self, id: int | str) -> bool:
        with self._lock:
            token = self._pending.get(id)
            return token.is_canceled() if token is not None else False

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
