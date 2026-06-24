import io
import json
import logging

from robot_lsp.application.logging_config import apply_log_level, configure_logging


class TestLoggingConfig:
    def test_configure_logging_writes_structured_json(self):
        stream = io.StringIO()
        configure_logging("info", stream=stream)

        logging.getLogger("robot_lsp").info("server started")

        payload = json.loads(stream.getvalue())
        assert payload["level"] == "info"
        assert payload["logger"] == "robot_lsp"
        assert payload["message"] == "server started"
        assert "time" in payload

    def test_apply_log_level_updates_robot_lsp_logger(self):
        configure_logging("warning", stream=io.StringIO())

        apply_log_level("debug")

        assert logging.getLogger("robot_lsp").level == logging.DEBUG
