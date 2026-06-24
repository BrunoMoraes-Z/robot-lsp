from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
from typing import Any


def test_stdio_server_minimal_completion_session():
    proc = subprocess.Popen(
        [sys.executable, "-m", "robot_lsp", "--log-level", "error"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )
    try:
        assert proc.stdin is not None
        assert proc.stdout is not None

        _send(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"capabilities": {}}})
        initialize = _receive(proc)
        assert initialize["id"] == 1
        assert initialize["result"]["serverInfo"] == {"name": "robot-lsp", "version": "0.1.0"}

        uri = "file:///c:/projects/integration.robot"
        _send(proc, {"jsonrpc": "2.0", "method": "initialized", "params": {}})
        _send(
            proc,
            {
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {
                    "textDocument": {
                        "uri": uri,
                        "languageId": "robotframework",
                        "version": 1,
                        "text": "*** Settings ***\n",
                    }
                },
            },
        )
        _send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "textDocument/completion",
                "params": {"textDocument": {"uri": uri}, "position": {"line": 1, "character": 0}},
            },
        )
        completion = _receive_response(proc, 2)
        labels = [item["label"] for item in completion["result"]["items"]]
        assert "Library" in labels
        assert "Resource" in labels

        _send(proc, {"jsonrpc": "2.0", "id": 3, "method": "shutdown"})
        shutdown = _receive_response(proc, 3)
        assert shutdown["result"] is None
        _send(proc, {"jsonrpc": "2.0", "method": "exit"})

        assert proc.wait(timeout=5) == 0
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)


def test_stdio_server_publishes_and_clears_diagnostics():
    proc = subprocess.Popen(
        [sys.executable, "-m", "robot_lsp", "--log-level", "error"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )
    client = _LspClient(proc)
    try:
        client.send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"capabilities": {}}})
        assert client.receive_response(1)["result"]["serverInfo"]["name"] == "robot-lsp"

        uri = "file:///c:/projects/diagnostics.robot"
        client.send({"jsonrpc": "2.0", "method": "initialized", "params": {}})
        client.send(
            {
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {
                    "textDocument": {
                        "uri": uri,
                        "languageId": "robotframework",
                        "version": 1,
                        "text": "*** Test Cases ***\nBroken\n    ELSE\n",
                    }
                },
            }
        )

        published = client.receive_method("textDocument/publishDiagnostics", timeout=5.0)
        assert published["params"]["uri"] == uri
        assert len(published["params"]["diagnostics"]) == 1
        assert published["params"]["diagnostics"][0]["code"] == "parse_error"

        client.send(
            {
                "jsonrpc": "2.0",
                "method": "textDocument/didChange",
                "params": {
                    "textDocument": {"uri": uri, "version": 2},
                    "contentChanges": [{"text": "*** Test Cases ***\nFixed\n    Log    ok\n"}],
                },
            }
        )
        cleared = client.receive_method("textDocument/publishDiagnostics", timeout=5.0)
        assert cleared["params"] == {"uri": uri, "diagnostics": []}

        client.send({"jsonrpc": "2.0", "id": 2, "method": "shutdown"})
        assert client.receive_response(2)["result"] is None
        client.send({"jsonrpc": "2.0", "method": "exit"})
        assert proc.wait(timeout=5) == 0
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)


def _send(proc: subprocess.Popen, message: dict[str, Any]) -> None:
    assert proc.stdin is not None
    body = json.dumps(message, separators=(",", ":")).encode("utf-8")
    proc.stdin.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body)
    proc.stdin.flush()


def _receive_response(proc: subprocess.Popen, id_value: int) -> dict[str, Any]:
    while True:
        message = _receive(proc)
        if message.get("id") == id_value:
            return message


def _receive(proc: subprocess.Popen) -> dict[str, Any]:
    assert proc.stdout is not None
    headers = bytearray()
    while not headers.endswith(b"\r\n\r\n"):
        chunk = proc.stdout.read(1)
        if not chunk:
            raise AssertionError("Server closed stdout while waiting for headers")
        headers.extend(chunk)
    content_length = None
    for line in headers.decode("ascii").split("\r\n"):
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())
            break
    assert content_length is not None
    body = proc.stdout.read(content_length)
    if not body:
        raise AssertionError("Server closed stdout while waiting for body")
    return json.loads(body.decode("utf-8"))


class _LspClient:
    def __init__(self, proc: subprocess.Popen) -> None:
        self.proc = proc
        self._messages: queue.Queue[dict[str, Any] | BaseException] = queue.Queue()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def send(self, message: dict[str, Any]) -> None:
        _send(self.proc, message)

    def receive_response(self, id_value: int, timeout: float = 5.0) -> dict[str, Any]:
        return self._receive_matching(lambda message: message.get("id") == id_value, timeout)

    def receive_method(self, method: str, timeout: float = 5.0) -> dict[str, Any]:
        return self._receive_matching(lambda message: message.get("method") == method, timeout)

    def _receive_matching(self, predicate, timeout: float) -> dict[str, Any]:
        pending: list[dict[str, Any]] = []
        try:
            while True:
                item = self._messages.get(timeout=timeout)
                if isinstance(item, BaseException):
                    raise item
                if predicate(item):
                    return item
                pending.append(item)
        except queue.Empty as exc:
            raise AssertionError(f"Timed out waiting for LSP message. Pending: {pending}") from exc

    def _read_loop(self) -> None:
        while self.proc.poll() is None:
            try:
                self._messages.put(_receive(self.proc))
            except BaseException as exc:
                self._messages.put(exc)
                return
