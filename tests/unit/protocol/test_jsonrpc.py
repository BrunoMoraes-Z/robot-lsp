import pytest

from robot_lsp.protocol.jsonrpc import (
    METHOD_NOT_FOUND,
    PARSE_ERROR,
    JsonRpcError,
    JsonRpcMessage,
    JsonRpcProtocolError,
    create_error_response,
    create_notification,
    create_request,
    create_response,
    encode_message,
    parse_message,
)


class TestJsonRpc:
    def test_json_rpc_request(self):
        message = parse_message(
            '{"jsonrpc":"2.0","id":1,"method":"textDocument/completion","params":{"x":1}}'
        )

        assert message.is_request
        assert not message.is_notification
        assert message.id == 1
        assert message.method == "textDocument/completion"
        assert message.params == {"x": 1}

    def test_json_rpc_notification(self):
        message = parse_message(
            '{"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"uri":"file:///a.robot"}}'
        )

        assert message.is_notification
        assert not message.is_request
        assert message.id is None
        assert message.method == "textDocument/didOpen"

    def test_json_rpc_response(self):
        message = parse_message('{"jsonrpc":"2.0","id":"abc","result":{"ok":true}}')

        assert message.is_response
        assert not message.is_error
        assert message.id == "abc"
        assert message.result == {"ok": True}

    def test_json_rpc_response_null_result(self):
        message = parse_message('{"jsonrpc":"2.0","id":1,"result":null}')

        assert message.is_response
        assert message.result is None

    def test_json_rpc_error(self):
        message = parse_message(
            '{"jsonrpc":"2.0","id":1,"error":{"code":-32601,"message":"Method not found","data":"x"}}'
        )

        assert message.is_response
        assert message.is_error
        assert message.error == JsonRpcError(
            code=METHOD_NOT_FOUND,
            message="Method not found",
            data="x",
        )

    def test_json_rpc_invalid_json(self):
        with pytest.raises(JsonRpcProtocolError) as exc:
            parse_message("{")

        assert exc.value.code == PARSE_ERROR

    def test_json_rpc_invalid_request(self):
        with pytest.raises(JsonRpcProtocolError):
            parse_message('{"jsonrpc":"1.0","id":1,"method":"x"}')

    def test_encode_request(self):
        encoded = encode_message(create_request("m", id=1, params={"a": "b"}))

        assert encoded == '{"jsonrpc":"2.0","id":1,"method":"m","params":{"a":"b"}}'

    def test_encode_notification(self):
        encoded = encode_message(create_notification("m", params=[1, 2]))

        assert encoded == '{"jsonrpc":"2.0","method":"m","params":[1,2]}'

    def test_encode_response(self):
        encoded = encode_message(create_response(1, {"ok": True}))


        assert encoded == '{"jsonrpc":"2.0","id":1,"result":{"ok":true}}'

    def test_encode_error_response(self):
        encoded = encode_message(create_error_response(1, METHOD_NOT_FOUND, "missing", "x"))

        assert encoded == '{"jsonrpc":"2.0","id":1,"error":{"code":-32601,"message":"missing","data":"x"}}'

    def test_encode_unicode_without_ascii_escaping(self):
        encoded = encode_message(JsonRpcMessage(method="m", params={"text": "olá 🤖"}))

        assert "olá 🤖" in encoded
