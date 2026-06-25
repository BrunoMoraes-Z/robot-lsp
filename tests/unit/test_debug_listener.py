"""Unit tests for the Robot LSP debug listener."""

from __future__ import annotations

import json
import queue
import socket
import threading
import time
from typing import Any
from unittest.mock import patch

import pytest

from robot_lsp.debug.listener import RobotLspDebugListener


def _make_listener(port: int, token: str) -> RobotLspDebugListener:
    """Create a listener instance bypassing __init__ socket setup."""
    listener = RobotLspDebugListener.__new__(RobotLspDebugListener)
    listener._token = token
    listener._breakpoints = {}
    listener._paused_commands: queue.Queue[dict[str, Any]] = queue.Queue()
    listener._closed = False
    listener._current_depth = 0
    listener._step_mode = None
    listener._paused_depth = 0
    sent: list[str] = []
    listener._sent = sent

    def fake_send(event: str, payload: dict[str, Any]) -> None:
        sent.append(json.dumps({"event": event, "payload": payload}))

    listener._send = fake_send  # type: ignore[method-assign]
    return listener


# ─── Listener API version ────────────────────────────────────────────────────

def test_robot_listener_api_version():
    assert RobotLspDebugListener.ROBOT_LISTENER_API_VERSION == 3


# ─── _set_breakpoints ────────────────────────────────────────────────────────

def test_set_breakpoints_stores_normalized_path(tmp_path):
    source = tmp_path / "suite.robot"
    listener = _make_listener(0, "tok")
    listener._set_breakpoints([{"source": str(source), "line": 3}])
    assert listener._breakpoints[listener._normalize_path(str(source))] == {3}


def test_set_breakpoints_multiple_lines(tmp_path):
    source = str(tmp_path / "suite.robot")
    listener = _make_listener(0, "tok")
    listener._set_breakpoints([{"source": source, "line": 1}, {"source": source, "line": 5}])
    assert listener._breakpoints[listener._normalize_path(source)] == {1, 5}


def test_set_breakpoints_multiple_sources(tmp_path):
    s1 = str(tmp_path / "a.robot")
    s2 = str(tmp_path / "b.robot")
    listener = _make_listener(0, "tok")
    listener._set_breakpoints([{"source": s1, "line": 2}, {"source": s2, "line": 7}])
    assert 2 in listener._breakpoints[listener._normalize_path(s1)]
    assert 7 in listener._breakpoints[listener._normalize_path(s2)]


def test_set_breakpoints_clears_old_breakpoints(tmp_path):
    source = str(tmp_path / "suite.robot")
    listener = _make_listener(0, "tok")
    listener._set_breakpoints([{"source": source, "line": 1}])
    listener._set_breakpoints([{"source": source, "line": 99}])
    assert listener._breakpoints[listener._normalize_path(source)] == {99}


def test_set_breakpoints_ignores_non_dict_entries():
    listener = _make_listener(0, "tok")
    listener._set_breakpoints(["invalid", 42, None])
    assert listener._breakpoints == {}


def test_set_breakpoints_ignores_missing_fields(tmp_path):
    listener = _make_listener(0, "tok")
    listener._set_breakpoints([{"source": str(tmp_path / "a.robot")}, {"line": 5}])
    assert listener._breakpoints == {}


# ─── _should_pause ───────────────────────────────────────────────────────────

def test_should_pause_at_breakpoint(tmp_path):
    source = str(tmp_path / "suite.robot")
    listener = _make_listener(0, "tok")
    listener._set_breakpoints([{"source": source, "line": 10}])
    listener._current_depth = 1
    result = listener._should_pause(source, 10)
    assert result == "breakpoint"


def test_should_not_pause_when_no_breakpoint_or_step(tmp_path):
    source = str(tmp_path / "suite.robot")
    listener = _make_listener(0, "tok")
    listener._set_breakpoints([{"source": source, "line": 10}])
    listener._current_depth = 1
    assert listener._should_pause(source, 5) is None


def test_should_pause_step_in_at_any_depth():
    listener = _make_listener(0, "tok")
    listener._step_mode = "step_in"
    listener._current_depth = 3
    listener._paused_depth = 2
    result = listener._should_pause("/some.robot", 1)
    assert result == "step"
    assert listener._step_mode is None  # cleared


def test_should_pause_next_at_same_depth():
    listener = _make_listener(0, "tok")
    listener._step_mode = "next"
    listener._current_depth = 2
    listener._paused_depth = 2
    result = listener._should_pause("/some.robot", 1)
    assert result == "step"
    assert listener._step_mode is None


def test_should_not_pause_next_at_deeper_depth():
    listener = _make_listener(0, "tok")
    listener._step_mode = "next"
    listener._current_depth = 3
    listener._paused_depth = 2
    assert listener._should_pause("/some.robot", 1) is None
    assert listener._step_mode == "next"  # not cleared


def test_should_pause_step_out_at_shallower_depth():
    listener = _make_listener(0, "tok")
    listener._step_mode = "step_out"
    listener._current_depth = 1
    listener._paused_depth = 2
    result = listener._should_pause("/some.robot", 1)
    assert result == "step"
    assert listener._step_mode is None


def test_should_not_pause_step_out_at_same_depth():
    listener = _make_listener(0, "tok")
    listener._step_mode = "step_out"
    listener._current_depth = 2
    listener._paused_depth = 2
    assert listener._should_pause("/some.robot", 1) is None


def test_should_pause_returns_none_without_source():
    listener = _make_listener(0, "tok")
    assert listener._should_pause(None, 5) is None
    assert listener._should_pause("/path.robot", None) is None


# ─── start_keyword / end_keyword ─────────────────────────────────────────────

class _MockKeywordData:
    def __init__(self, source: str | None = "/suite.robot", lineno: int | None = 10, name: str = "My Keyword"):
        self.source = source
        self.lineno = lineno
        self.name = name


def test_start_keyword_increments_depth():
    listener = _make_listener(0, "tok")
    data = _MockKeywordData(source=None)  # no source → won't pause
    listener.start_keyword(data, object())
    assert listener._current_depth == 1


def test_end_keyword_decrements_depth():
    listener = _make_listener(0, "tok")
    listener._current_depth = 2
    listener.end_keyword(_MockKeywordData(), object())
    assert listener._current_depth == 1


def test_start_keyword_pauses_at_breakpoint(tmp_path):
    source = str(tmp_path / "suite.robot")
    listener = _make_listener(0, "tok")
    listener._set_breakpoints([{"source": source, "line": 10}])
    # Simulate continue command to unblock _command_loop
    listener._paused_commands.put({"command": "continue"})
    listener.start_keyword(_MockKeywordData(source=source, lineno=10), object())
    events = [json.loads(e)["event"] for e in listener._sent]
    assert "paused" in events
    assert "continued" in events


def test_start_keyword_does_not_pause_on_other_line(tmp_path):
    source = str(tmp_path / "suite.robot")
    listener = _make_listener(0, "tok")
    listener._set_breakpoints([{"source": source, "line": 10}])
    listener.start_keyword(_MockKeywordData(source=source, lineno=5), object())
    assert listener._sent == []


def test_start_keyword_pauses_on_step_in():
    listener = _make_listener(0, "tok")
    listener._step_mode = "step_in"
    listener._paused_commands.put({"command": "continue"})
    listener.start_keyword(_MockKeywordData(source="/any.robot", lineno=1), object())
    events = [json.loads(e)["event"] for e in listener._sent]
    assert "paused" in events
    paused_payload = next(
        json.loads(e)["payload"] for e in listener._sent if json.loads(e)["event"] == "paused"
    )
    assert paused_payload["reason"] == "step"


# ─── _command_loop ───────────────────────────────────────────────────────────

def test_command_loop_continue_clears_step_mode():
    listener = _make_listener(0, "tok")
    listener._step_mode = "next"
    listener._current_depth = 2
    listener._paused_commands.put({"command": "continue"})
    listener._command_loop()
    assert listener._step_mode is None
    events = [json.loads(e)["event"] for e in listener._sent]
    assert "continued" in events


def test_command_loop_next_sets_step_mode():
    listener = _make_listener(0, "tok")
    listener._current_depth = 1
    listener._paused_commands.put({"command": "next"})
    listener._command_loop()
    assert listener._step_mode == "next"
    assert listener._paused_depth == 1


def test_command_loop_step_in_sets_step_mode():
    listener = _make_listener(0, "tok")
    listener._current_depth = 2
    listener._paused_commands.put({"command": "step_in"})
    listener._command_loop()
    assert listener._step_mode == "step_in"
    assert listener._paused_depth == 2


def test_command_loop_step_out_sets_step_mode():
    listener = _make_listener(0, "tok")
    listener._current_depth = 3
    listener._paused_commands.put({"command": "step_out"})
    listener._command_loop()
    assert listener._step_mode == "step_out"
    assert listener._paused_depth == 3


def test_command_loop_sends_continued_on_step():
    listener = _make_listener(0, "tok")
    listener._current_depth = 1
    listener._paused_commands.put({"command": "next"})
    listener._command_loop()
    events = [json.loads(e)["event"] for e in listener._sent]
    assert "continued" in events


def test_command_loop_evaluate_invokes_evaluate():
    listener = _make_listener(0, "tok")
    evaluated: list[tuple[str, Any]] = []

    def fake_evaluate(expr: str, req_id: Any) -> None:
        evaluated.append((expr, req_id))
        listener._paused_commands.put({"command": "continue"})

    listener._evaluate = fake_evaluate  # type: ignore[method-assign]
    listener._current_depth = 1
    listener._paused_commands.put({"command": "evaluate", "expression": "${VAR}", "requestId": 7})
    listener._command_loop()
    assert evaluated == [("${VAR}", 7)]


# ─── _normalize_path ─────────────────────────────────────────────────────────

def test_normalize_path_returns_string(tmp_path):
    listener = _make_listener(0, "tok")
    result = listener._normalize_path(str(tmp_path / "file.robot"))
    assert isinstance(result, str)


def test_normalize_path_is_absolute():
    import os
    listener = _make_listener(0, "tok")
    result = listener._normalize_path("relative/path.robot")
    assert os.path.isabs(result)


def test_normalize_path_consistent_for_same_input(tmp_path):
    listener = _make_listener(0, "tok")
    p = str(tmp_path / "suite.robot")
    assert listener._normalize_path(p) == listener._normalize_path(p)


# ─── Full socket round-trip ───────────────────────────────────────────────────

class _SocketServer:
    """Minimal TCP server for testing the listener's connection."""

    def __init__(self) -> None:
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(("127.0.0.1", 0))
        self._server.listen(1)
        self.port: int = self._server.getsockname()[1]
        self.received: list[dict[str, Any]] = []
        self._client: socket.socket | None = None
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        self._client, _ = self._server.accept()
        self._client.settimeout(5.0)
        buf = b""
        while True:
            try:
                chunk = self._client.recv(4096)
            except OSError:
                break
            if not chunk:
                break
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                text = line.decode("utf-8").strip()
                if text:
                    self.received.append(json.loads(text))

    def send(self, obj: dict[str, Any]) -> None:
        if self._client:
            self._client.sendall((json.dumps(obj) + "\n").encode("utf-8"))

    def close(self) -> None:
        if self._client:
            try:
                self._client.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._client.close()
        self._server.close()


def _wait(condition: Any, timeout: float = 2.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.01)
    return False


@pytest.fixture
def server():
    srv = _SocketServer()
    yield srv
    # Best-effort cleanup; tests may have already called srv.close()
    try:
        srv.close()
    except Exception:
        pass


def test_listener_sends_started_event(server):
    token = "test-token"
    with patch("robot_lsp.debug.listener.BuiltIn"):
        listener = RobotLspDebugListener(str(server.port), token)
    assert _wait(lambda: len(server.received) >= 1), "listener_started not received within timeout"
    assert server.received[0]["event"] == "listener_started"
    # Close server side to cleanly terminate the listener's reader thread
    server.close()
    listener._closed = True


def test_listener_responds_to_set_breakpoints(server, tmp_path):
    token = "test-token"
    source = str(tmp_path / "suite.robot")
    with patch("robot_lsp.debug.listener.BuiltIn"):
        listener = RobotLspDebugListener(str(server.port), token)
    assert _wait(lambda: len(server.received) >= 1)
    server.send({"token": token, "command": "set_breakpoints", "breakpoints": [{"source": source, "line": 5}]})
    assert _wait(lambda: listener._breakpoints != {}), "breakpoints not set within timeout"
    assert 5 in listener._breakpoints[listener._normalize_path(source)]
    server.close()
    listener._closed = True


def test_listener_ignores_wrong_token(server):
    token = "real-token"
    with patch("robot_lsp.debug.listener.BuiltIn"):
        listener = RobotLspDebugListener(str(server.port), token)
    assert _wait(lambda: len(server.received) >= 1)
    server.send({"token": "wrong-token", "command": "continue"})
    time.sleep(0.05)
    assert listener._paused_commands.empty()
    server.close()
    listener._closed = True
