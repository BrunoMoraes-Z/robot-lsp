from __future__ import annotations

import threading
from collections.abc import Callable

from robot_lsp.domain.diagnostics import DiagnosticSeverity, LspDiagnostic
from robot_lsp.domain.models import RobotDiagnostic

from .parse_service import ParseService


PublishDiagnostics = Callable[[str, list[LspDiagnostic]], None]


class DiagnosticService:
    DEBOUNCE_SECONDS = 0.3

    def __init__(
        self,
        parse_service: ParseService,
        publisher: PublishDiagnostics,
        *,
        debounce_seconds: float | None = None,
    ) -> None:
        self._parse_service = parse_service
        self._publisher = publisher
        self._debounce_seconds = (
            self.DEBOUNCE_SECONDS if debounce_seconds is None else debounce_seconds
        )
        self._timers: dict[str, threading.Timer] = {}
        self._last_diagnostics: dict[str, list[LspDiagnostic]] = {}
        self._lock = threading.RLock()

    def schedule_diagnostics(self, uri: str) -> None:
        self.cancel_pending(uri)
        timer = threading.Timer(self._debounce_seconds, self.compute_and_publish, args=(uri,))
        with self._lock:
            self._timers[uri] = timer
        timer.start()

    def compute_and_publish(self, uri: str) -> None:
        with self._lock:
            self._timers.pop(uri, None)

        result = self._parse_service.parse_uri(uri)
        diagnostics = [] if result is None else [_to_lsp(item) for item in result.errors]
        self.publish_if_changed(uri, diagnostics)

    def flush(self, uri: str) -> None:
        self.cancel_pending(uri)
        self.compute_and_publish(uri)

    def publish_if_changed(self, uri: str, diagnostics: list[LspDiagnostic]) -> None:
        with self._lock:
            if self._last_diagnostics.get(uri) == diagnostics:
                return
            self._last_diagnostics[uri] = diagnostics
        self._publisher(uri, diagnostics)

    def cancel_pending(self, uri: str) -> bool:
        with self._lock:
            timer = self._timers.pop(uri, None)
        if timer is None:
            return False
        timer.cancel()
        return True

    def clear(self, uri: str) -> None:
        self.cancel_pending(uri)
        self.publish_if_changed(uri, [])


def _to_lsp(diagnostic: RobotDiagnostic) -> LspDiagnostic:
    return LspDiagnostic(
        range=diagnostic.range,
        severity=_severity(diagnostic.severity),
        message=diagnostic.message,
        source="robot-lsp",
        code=diagnostic.code,
    )


def _severity(severity: str) -> DiagnosticSeverity:
    if severity == "warning":
        return DiagnosticSeverity.WARNING
    if severity == "info":
        return DiagnosticSeverity.INFORMATION
    return DiagnosticSeverity.ERROR
