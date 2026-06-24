from __future__ import annotations

import io

from robot_lsp.protocol.transport_stdio import TransportStdio


class ChunkedBytesIO(io.BytesIO):
    def __init__(self, initial_bytes: bytes, chunk_size: int) -> None:
        super().__init__(initial_bytes)
        self._chunk_size = chunk_size

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = self._chunk_size
        return super().read(min(size, self._chunk_size))


class TestTransportStdio:
    def test_transport_content_length(self):
        writer = io.BytesIO()
        transport = TransportStdio(reader=io.BytesIO(), writer=writer)

        transport.write_message('{"jsonrpc":"2.0","method":"m"}')

        assert writer.getvalue() == b'Content-Length: 30\r\n\r\n{"jsonrpc":"2.0","method":"m"}'

    def test_transport_read_message(self):
        body = b'{"jsonrpc":"2.0","method":"m"}'
        reader = io.BytesIO(b"Content-Length: 30\r\n\r\n" + body)
        transport = TransportStdio(reader=reader, writer=io.BytesIO())

        assert transport.read_message() == body.decode("utf-8")

    def test_transport_partial_message(self):
        body = b'{"jsonrpc":"2.0","method":"m"}'
        reader = ChunkedBytesIO(b"Content-Length: 30\r\n\r\n" + body, chunk_size=3)
        transport = TransportStdio(reader=reader, writer=io.BytesIO())

        assert transport.read_message() == body.decode("utf-8")

    def test_transport_multiple_messages(self):
        body1 = b'{"jsonrpc":"2.0","method":"a"}'
        body2 = b'{"jsonrpc":"2.0","method":"b"}'
        reader = io.BytesIO(
            b"Content-Length: 30\r\n\r\n"
            + body1
            + b"Content-Length: 30\r\n\r\n"
            + body2
        )
        transport = TransportStdio(reader=reader, writer=io.BytesIO())

        assert transport.read_message() == body1.decode("utf-8")
        assert transport.read_message() == body2.decode("utf-8")

    def test_transport_multibyte_body_length(self):
        message = '{"jsonrpc":"2.0","method":"m","params":{"text":"olá 🤖"}}'
        writer = io.BytesIO()
        transport = TransportStdio(reader=io.BytesIO(), writer=writer)

        transport.write_message(message)

        header, body = writer.getvalue().split(b"\r\n\r\n", 1)
        assert header == f"Content-Length: {len(message.encode('utf-8'))}".encode("ascii")
        assert body.decode("utf-8") == message

    def test_transport_ignores_content_type(self):
        body = b'{"jsonrpc":"2.0","method":"m"}'
        reader = io.BytesIO(
            b"Content-Length: 30\r\nContent-Type: application/vscode-jsonrpc; charset=utf-8\r\n\r\n"
            + body
        )
        transport = TransportStdio(reader=reader, writer=io.BytesIO())

        assert transport.read_message() == body.decode("utf-8")
