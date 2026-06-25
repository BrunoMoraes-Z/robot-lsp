from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def test_worker_subprocess_ping_and_shutdown():
    proc = _start_worker()
    try:
        _send(proc, {"jsonrpc": "2.0", "id": 1, "method": "worker/ping"})
        response = _receive(proc)

        assert response["id"] == 1
        assert response["result"]["ok"] is True
        assert isinstance(response["result"]["pid"], int)
        assert response["result"]["pid"] != 0

        _send(proc, {"jsonrpc": "2.0", "id": 2, "method": "shutdown"})
        assert _receive(proc)["result"] is None
        assert proc.wait(timeout=5) == 0
    finally:
        _stop_worker(proc)


def test_worker_subprocess_scans_workspace(tmp_path: Path):
    (tmp_path / "suite.robot").write_text(
        "*** Variables ***\n"
        "${MESSAGE}    hello\n"
        "*** Keywords ***\n"
        "My Keyword\n"
        "    Log    ${MESSAGE}\n",
        encoding="utf-8",
    )
    (tmp_path / "resource.resource").write_text(
        "*** Keywords ***\n"
        "Resource Keyword\n"
        "    No Operation\n",
        encoding="utf-8",
    )

    proc = _start_worker()
    try:
        _send(proc, {"jsonrpc": "2.0", "id": 1, "method": "workspace/scan", "params": {"root": str(tmp_path)}})
        response = _receive(proc)

        assert response["id"] == 1
        assert response["result"] == {"files": 2, "keywords": 2, "variables": 1}

        _send(proc, {"jsonrpc": "2.0", "id": 2, "method": "shutdown"})
        assert _receive(proc)["result"] is None
        assert proc.wait(timeout=5) == 0
    finally:
        _stop_worker(proc)


def _start_worker() -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-m", "robot_lsp.worker"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )


def _stop_worker(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.kill()
        proc.wait(timeout=5)


def _send(proc: subprocess.Popen, message: dict[str, Any]) -> None:
    assert proc.stdin is not None
    body = json.dumps(message, separators=(",", ":")).encode("utf-8")
    proc.stdin.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body)
    proc.stdin.flush()


def _receive(proc: subprocess.Popen) -> dict[str, Any]:
    assert proc.stdout is not None
    headers = bytearray()
    while not headers.endswith(b"\r\n\r\n"):
        chunk = proc.stdout.read(1)
        if not chunk:
            stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr is not None else ""
            raise AssertionError(f"Worker closed stdout while waiting for headers. stderr={stderr}")
        headers.extend(chunk)
    content_length = None
    for line in headers.decode("ascii").split("\r\n"):
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())
            break
    assert content_length is not None
    body = proc.stdout.read(content_length)
    if not body:
        raise AssertionError("Worker closed stdout while waiting for body")
    return json.loads(body.decode("utf-8"))
