"""Robot Framework listener used by the VS Code debug adapter."""

from __future__ import annotations

import json
import os
import queue
import socket
import threading
from typing import Any

from robot.libraries.BuiltIn import BuiltIn


class RobotLspDebugListener:
    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self, port: str, token: str) -> None:
        self._token = token
        self._socket = socket.create_connection(("127.0.0.1", int(port)), timeout=10)
        self._socket.settimeout(None)
        self._reader = self._socket.makefile("r", encoding="utf-8", newline="\n")
        self._writer = self._socket.makefile("w", encoding="utf-8", newline="\n")
        self._breakpoints: dict[str, set[int]] = {}
        self._paused_commands: queue.Queue[dict[str, Any]] = queue.Queue()
        self._closed = False
        self._current_depth = 0
        self._step_mode: str | None = None
        self._paused_depth = 0
        self._reader_thread = threading.Thread(target=self._read_commands, daemon=True)
        self._reader_thread.start()
        self._send("listener_started", {})

    def start_suite(self, data: Any, result: Any) -> None:
        self._send("suite_started", {"name": data.name})

    def end_suite(self, data: Any, result: Any) -> None:
        self._send(
            "suite_ended",
            {"name": data.name, "status": result.status, "message": result.message},
        )

    def start_test(self, data: Any, result: Any) -> None:
        self._send("test_started", {"name": data.name, "longname": data.longname})

    def end_test(self, data: Any, result: Any) -> None:
        self._send(
            "test_ended",
            {
                "name": data.name,
                "longname": data.longname,
                "status": result.status,
                "message": result.message,
            },
        )

    def log_message(self, message: Any) -> None:
        self._send(
            "log_message",
            {"level": message.level, "message": message.message},
        )

    def start_keyword(self, data: Any, result: Any) -> None:
        self._current_depth += 1
        source = getattr(data, "source", None)
        lineno = getattr(data, "lineno", None)
        reason = self._should_pause(source, lineno)
        if reason is None:
            return
        self._send(
            "paused",
            {
                "reason": reason,
                "source": source,
                "line": lineno,
                "name": getattr(data, "name", "Robot Keyword"),
            },
        )
        self._command_loop()

    def end_keyword(self, data: Any, result: Any) -> None:
        self._current_depth -= 1

    def close(self) -> None:
        self._closed = True
        try:
            self._send("listener_closed", {})
        except Exception:
            pass
        finally:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._reader.close()
            self._writer.close()
            self._socket.close()

    def _should_pause(self, source: Any, lineno: Any) -> str | None:
        if self._step_mode == "step_in":
            self._step_mode = None
            return "step"
        if self._step_mode == "next" and self._current_depth <= self._paused_depth:
            self._step_mode = None
            return "step"
        if self._step_mode == "step_out" and self._current_depth < self._paused_depth:
            self._step_mode = None
            return "step"
        if not isinstance(source, str) or not isinstance(lineno, int):
            return None
        if lineno in self._breakpoints.get(self._normalize_path(source), set()):
            return "breakpoint"
        return None

    def _send(self, event: str, payload: dict[str, Any]) -> None:
        self._writer.write(
            json.dumps(
                {"token": self._token, "event": event, "payload": payload},
                separators=(",", ":"),
            )
            + "\n"
        )
        self._writer.flush()

    def _command_loop(self) -> None:
        self._paused_depth = self._current_depth
        while True:
            message = self._paused_commands.get()
            command = message.get("command")
            if command == "continue":
                self._step_mode = None
                self._send("continued", {})
                return
            if command in ("next", "step_in", "step_out"):
                self._step_mode = command
                self._send("continued", {})
                return
            if command == "evaluate":
                self._evaluate(str(message.get("expression", "")), message.get("requestId"))

    def _read_commands(self) -> None:
        while not self._closed:
            line = self._reader.readline()
            if line == "":
                return
            message = json.loads(line)
            if message.get("token") != self._token:
                continue
            if message.get("command") == "set_breakpoints":
                self._set_breakpoints(message.get("breakpoints", []))
                continue
            self._paused_commands.put(message)

    def _set_breakpoints(self, breakpoints: Any) -> None:
        result: dict[str, set[int]] = {}
        if isinstance(breakpoints, list):
            for breakpoint in breakpoints:
                if not isinstance(breakpoint, dict):
                    continue
                source = breakpoint.get("source")
                line = breakpoint.get("line")
                if isinstance(source, str) and isinstance(line, int):
                    result.setdefault(self._normalize_path(source), set()).add(line)
        self._breakpoints = result

    def _evaluate(self, expression: str, request_id: Any) -> None:
        try:
            value = BuiltIn().get_variable_value(expression)
            if value is None and not expression.startswith("${"):
                value = BuiltIn().get_variable_value("${" + expression + "}")
            self._send(
                "evaluate_response",
                {"requestId": request_id, "success": True, "result": repr(value)},
            )
        except Exception as exc:  # Robot runtime errors should be reported to DAP.
            self._send(
                "evaluate_response",
                {"requestId": request_id, "success": False, "message": str(exc)},
            )

    def _normalize_path(self, path: str) -> str:
        return os.path.normcase(os.path.abspath(path))
