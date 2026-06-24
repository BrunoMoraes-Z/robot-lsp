from __future__ import annotations

import sys
import threading
from typing import BinaryIO


class TransportStdio:
    def __init__(
        self,
        reader: BinaryIO | None = None,
        writer: BinaryIO | None = None,
    ) -> None:
        self._reader = reader or sys.stdin.buffer
        self._writer = writer or sys.stdout.buffer
        self._write_lock = threading.Lock()

    def read_message(self) -> str | None:
        headers = self._read_headers()
        if headers is None:
            return None

        content_length = headers.get("content-length")
        if content_length is None:
            raise ValueError("Missing Content-Length header")

        try:
            length = int(content_length)
        except ValueError as exc:
            raise ValueError("Invalid Content-Length header") from exc

        body = self._read_exact(length)
        if body is None:
            return None
        return body.decode("utf-8")

    def write_message(self, message: str) -> None:
        body = message.encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        with self._write_lock:
            self._writer.write(header)
            self._writer.write(body)
            self._writer.flush()

    def _read_headers(self) -> dict[str, str] | None:
        raw = bytearray()
        while not raw.endswith(b"\r\n\r\n"):
            chunk = self._reader.read(1)
            if not chunk:
                return None if not raw else _raise_eof_in_header()
            raw.extend(chunk)

        header_text = raw.decode("ascii")
        headers: dict[str, str] = {}
        for line in header_text.split("\r\n"):
            if not line:
                continue
            if ":" not in line:
                raise ValueError(f"Invalid header line: {line}")
            name, value = line.split(":", 1)
            headers[name.strip().lower()] = value.strip()
        return headers

    def _read_exact(self, length: int) -> bytes | None:
        if length < 0:
            raise ValueError("Content-Length must be non-negative")

        chunks = bytearray()
        while len(chunks) < length:
            chunk = self._reader.read(length - len(chunks))
            if not chunk:
                return None
            chunks.extend(chunk)
        return bytes(chunks)


def _raise_eof_in_header() -> None:
    raise EOFError("Unexpected EOF while reading LSP headers")
