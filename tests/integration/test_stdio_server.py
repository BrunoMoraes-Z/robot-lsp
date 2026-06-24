from __future__ import annotations

import json
import subprocess
import sys
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
