from pathlib import Path

from robot_lsp.application.configuration import ConfigurationService


class TestConfigurationService:
    def test_default_config(self):
        service = ConfigurationService()

        assert service.config.import_paths == ()
        assert service.config.log_level == "info"
        assert service.config.diagnostics.enable is True
        assert service.config.completion.snippets is True
        assert service.config.variables == {}

    def test_update_from_direct_settings(self):
        service = ConfigurationService()

        config = service.update(
            {
                "importPaths": ["./resources", ""],
                "logLevel": "debug",
                "diagnostics": {"enable": False},
                "completion": {"snippets": False},
                "variables": {"EXECDIR": "/workspace", "ENV": "dev"},
            }
        )

        assert config.import_paths == (Path("./resources").expanduser(),)
        assert config.log_level == "debug"
        assert config.diagnostics.enable is False
        assert config.completion.snippets is False
        assert config.variables == {"EXECDIR": "/workspace", "ENV": "dev"}

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

    def test_workspace_config_applies_to_matching_uri(self):
        service = ConfigurationService()
        service.update({"diagnostics": {"enable": False}}, scope_uri="file:///c:/projects/app")

        assert service.config.diagnostics.enable is True
        assert service.config_for_uri("file:///c:/projects/app/tests/example.robot").diagnostics.enable is False
        assert service.config_for_uri("file:///c:/projects/other/example.robot").diagnostics.enable is True

    def test_most_specific_workspace_config_wins(self):
        service = ConfigurationService()
        service.update({"completion": {"snippets": False}}, scope_uri="file:///c:/projects/app")
        service.update({"completion": {"snippets": True}}, scope_uri="file:///c:/projects/app/nested")

        config = service.config_for_uri("file:///c:/projects/app/nested/example.robot")

        assert config.completion.snippets is True

    def test_workspace_config_inherits_global_changes(self):
        service = ConfigurationService()
        service.update({"diagnostics": {"enable": False}}, scope_uri="file:///c:/projects/app")

        service.update({"logLevel": "debug"})

        config = service.config_for_uri("file:///c:/projects/app/example.robot")
        assert config.log_level == "debug"
        assert config.diagnostics.enable is False

    def test_workspace_variables_apply_to_matching_uri(self):
        service = ConfigurationService()
        service.update({"variables": {"LOCAL": "value"}}, scope_uri="file:///c:/projects/app")

        assert service.config_for_uri("file:///c:/projects/app/tests/example.robot").variables == {"LOCAL": "value"}
        assert service.config_for_uri("file:///c:/projects/other/example.robot").variables == {}
