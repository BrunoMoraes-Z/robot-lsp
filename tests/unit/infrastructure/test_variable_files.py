import builtins

from robot_lsp.infrastructure.robotframework.variable_files import parse_yaml_variable_file


def test_parse_yaml_variable_file_returns_empty_when_pyyaml_is_missing(tmp_path, monkeypatch):
    path = tmp_path / "vars.yaml"
    path.write_text("USER:\n  name: Ana\n", encoding="utf-8")
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("missing yaml")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    assert parse_yaml_variable_file(path) == []
