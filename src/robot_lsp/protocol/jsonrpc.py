from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Final

JSONRPC_VERSION: Final = "2.0"

PARSE_ERROR: Final = -32700
INVALID_REQUEST: Final = -32600
METHOD_NOT_FOUND: Final = -32601
INVALID_PARAMS: Final = -32602
INTERNAL_ERROR: Final = -32603
SERVER_NOT_INITIALIZED: Final = -32002
SERVER_SHUTTING_DOWN: Final = -32003

_UNSET = object()


class JsonRpcProtocolError(Exception):
    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


@dataclass(frozen=True)
class JsonRpcError:
    code: int
    message: str
    data: Any = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            payload["data"] = self.data
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> JsonRpcError:
        code = payload.get("code")
        message = payload.get("message")
        if not isinstance(code, int) or not isinstance(message, str):
            raise JsonRpcProtocolError(INVALID_REQUEST, "Invalid error object")
        return cls(code=code, message=message, data=payload.get("data"))


@dataclass(frozen=True)
class JsonRpcMessage:
    jsonrpc: str = JSONRPC_VERSION
    id: int | str | None = None
    method: str | None = None
    params: dict[str, Any] | list[Any] | None = None
    result: Any = _UNSET
    error: JsonRpcError | None = None

    @property
    def is_request(self) -> bool:
        return self.method is not None and self.id is not None

    @property
    def is_notification(self) -> bool:
        return self.method is not None and self.id is None

    @property
    def is_response(self) -> bool:
        return self.method is None and self.id is not None and (
            self.result is not _UNSET or self.error is not None
        )

    @property
    def is_error(self) -> bool:
        return self.error is not None


def parse_message(json_str: str) -> JsonRpcMessage:
    try:
        payload = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise JsonRpcProtocolError(PARSE_ERROR, "Parse error", str(exc)) from exc

    if not isinstance(payload, dict):
        raise JsonRpcProtocolError(INVALID_REQUEST, "Invalid request")

    if payload.get("jsonrpc") != JSONRPC_VERSION:
        raise JsonRpcProtocolError(INVALID_REQUEST, "Invalid JSON-RPC version")

    if "method" in payload:
        return _parse_request_or_notification(payload)

    return _parse_response(payload)


def encode_message(message: JsonRpcMessage) -> str:
    payload: dict[str, Any] = {"jsonrpc": JSONRPC_VERSION}

    if message.method is not None:
        if message.id is not None:
            payload["id"] = message.id
        payload["method"] = message.method
        if message.params is not None:
            payload["params"] = message.params
    else:
        payload["id"] = message.id
        if message.error is not None:
            payload["error"] = message.error.to_dict()
        elif message.result is not _UNSET:
            payload["result"] = message.result
        else:
            raise JsonRpcProtocolError(INVALID_REQUEST, "Response requires result or error")

    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def create_request(
    method: str,
    *,
    id: int | str,
    params: dict[str, Any] | list[Any] | None = None,
) -> JsonRpcMessage:
    return JsonRpcMessage(id=id, method=method, params=params)


def create_notification(
    method: str,
    *,
    params: dict[str, Any] | list[Any] | None = None,
) -> JsonRpcMessage:
    return JsonRpcMessage(method=method, params=params)


def create_response(id: int | str, result: Any = None) -> JsonRpcMessage:
    return JsonRpcMessage(id=id, result=result)


def create_error_response(
    id: int | str | None,
    code: int,
    message: str,
    data: Any = None,
) -> JsonRpcMessage:
    return JsonRpcMessage(id=id, error=JsonRpcError(code=code, message=message, data=data))


def protocol_error_to_response(
    error: JsonRpcProtocolError,
    *,
    id: int | str | None = None,
) -> JsonRpcMessage:
    return create_error_response(id, error.code, error.message, error.data)


def _parse_request_or_notification(payload: dict[str, Any]) -> JsonRpcMessage:
    method = payload.get("method")
    if not isinstance(method, str):
        raise JsonRpcProtocolError(INVALID_REQUEST, "Method must be a string")

    id_value = payload.get("id")
    if "id" in payload and not _valid_id(id_value):
        raise JsonRpcProtocolError(INVALID_REQUEST, "Invalid id")

    params = payload.get("params")
    if params is not None and not isinstance(params, (dict, list)):
        raise JsonRpcProtocolError(INVALID_REQUEST, "Params must be an object or array")

    return JsonRpcMessage(id=id_value, method=method, params=params)


def _parse_response(payload: dict[str, Any]) -> JsonRpcMessage:
    if "id" not in payload:
        raise JsonRpcProtocolError(INVALID_REQUEST, "Response requires id")

    id_value = payload.get("id")
    if not _valid_id(id_value):
        raise JsonRpcProtocolError(INVALID_REQUEST, "Invalid id")

    has_result = "result" in payload
    has_error = "error" in payload
    if has_result == has_error:
        raise JsonRpcProtocolError(INVALID_REQUEST, "Response requires exactly one of result or error")

    if has_error:
        error_payload = payload["error"]
        if not isinstance(error_payload, dict):
            raise JsonRpcProtocolError(INVALID_REQUEST, "Invalid error object")
        return JsonRpcMessage(id=id_value, error=JsonRpcError.from_dict(error_payload))

    return JsonRpcMessage(id=id_value, result=payload.get("result"))


def _valid_id(id_value: Any) -> bool:
    return id_value is None or isinstance(id_value, (int, str))
