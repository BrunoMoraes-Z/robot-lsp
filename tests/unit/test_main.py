from __future__ import annotations

import io

from robot_lsp.main import main, run_lsp_loop
from robot_lsp.protocol.jsonrpc import create_notification, create_request, encode_message, parse_message
from robot_lsp.protocol.transport_stdio import TransportStdio


class TestMain:
    def test_main_version(self, capsys):
        assert main(["--version"]) == 0

        assert capsys.readouterr().out == "robot-lsp 0.1.0\n"

    def test_run_lsp_loop_handles_minimal_session(self):
        writer = io.BytesIO()
        transport = TransportStdio(
            reader=io.BytesIO(
                _frame(encode_message(create_request("initialize", id=1, params={"capabilities": {}})))
                + _frame(encode_message(create_request("shutdown", id=2)))
                + _frame(encode_message(create_notification("exit")))
            ),
            writer=writer,
        )

        assert run_lsp_loop(transport=transport) == 0

        messages = _read_framed_messages(writer.getvalue())
        assert [message.id for message in messages] == [1, 2]
        assert messages[0].result["serverInfo"] == {"name": "robot-lsp", "version": "0.1.0"}
        assert messages[1].result is None

    def test_run_lsp_loop_returns_protocol_error_response(self):
        writer = io.BytesIO()
        transport = TransportStdio(
            reader=io.BytesIO(_frame('{"jsonrpc":"2.0","method":1,"id":1}')),
            writer=writer,
        )

        assert run_lsp_loop(transport=transport) == 0

        messages = _read_framed_messages(writer.getvalue())
        assert len(messages) == 1
        assert messages[0].error is not None
        assert messages[0].error.message == "Method must be a string"


def _frame(message: str) -> bytes:
    body = message.encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body


def _read_framed_messages(raw: bytes):
    transport = TransportStdio(reader=io.BytesIO(raw), writer=io.BytesIO())
    messages = []
    while True:
        message = transport.read_message()
        if message is None:
            return messages
        messages.append(parse_message(message))
