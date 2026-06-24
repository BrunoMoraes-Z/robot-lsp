from pathlib import Path

from robot_lsp.application.configuration import ConfigurationService


class TestConfigurationService:
    def test_default_config(self):
        service = ConfigurationService()

        assert service.config.import_paths == ()
        assert service.config.log_level == "info"
        assert service.config.diagnostics.enable is True
        assert service.config.completion.snippets is True

    def test_update_from_direct_settings(self):
        service = ConfigurationService()

        config = service.update(
            {
                "importPaths": ["./resources", ""],
                "logLevel": "debug",
                "diagnostics": {"enable": False},
                "completion": {"snippets": False},
            }
        )

        assert config.import_paths == (Path("./resources").expanduser(),)
        assert config.log_level == "debug"
        assert config.diagnostics.enable is False
        assert config.completion.snippets is False

    def test_update_from_nested_robot_lsp_settings(self):
        service = ConfigurationService()

        config = service.update({"robot": {"lsp": {"diagnostics": {"enable": False}}}})

        assert config.diagnostics.enable is False

    def test_invalid_values_keep_previous_config(self):
        service = ConfigurationService()
        service.update({"logLevel": "debug", "diagnostics": {"enable": False}})

        config = service.update({"logLevel": "verbose", "diagnostics": {"enable": "no"}})

        assert config.log_level == "debug"
        assert config.diagnostics.enable is False
