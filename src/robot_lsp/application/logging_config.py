from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import TextIO

from robot_lsp.application.configuration import LogLevel


LOG_LEVELS: dict[LogLevel, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


class StructuredLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "time": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"))


def configure_logging(log_level: LogLevel, stream: TextIO | None = None) -> None:
    logger = logging.getLogger("robot_lsp")
    logger.handlers.clear()
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(StructuredLogFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    apply_log_level(log_level)


def apply_log_level(log_level: LogLevel) -> None:
    logging.getLogger("robot_lsp").setLevel(LOG_LEVELS[log_level])
