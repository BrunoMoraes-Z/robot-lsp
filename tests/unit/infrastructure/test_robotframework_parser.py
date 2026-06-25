from pathlib import Path

from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser


FIXTURES = Path(__file__).parents[2] / "integration" / "fixtures"


class TestRobotFrameworkParser:
    def test_parse_basic_suite(self):
        result = RobotFrameworkParser().parse_file(FIXTURES / "basic_suite.robot")

        assert result.errors == []
        assert result.suite is not None
        assert result.suite.name == "basic_suite"
        assert result.suite.doc == "Suite documentation"
        assert result.suite.metadata == {"Owner": "Platform Team"}
        assert [item.name for item in result.suite.test_cases] == ["My Test"]
        assert [item.name for item in result.suite.keywords] == ["My Keyword"]

    def test_parse_settings(self):
        result = RobotFrameworkParser().parse_file(FIXTURES / "settings.robot")

        settings = result.suite.settings

        assert settings.suite_setup == "Log    suite setup"
        assert settings.suite_teardown == "Log    suite teardown"
        assert settings.test_setup == "Log    test setup"
        assert settings.test_teardown == "Log    test teardown"
        assert settings.test_template == "Template Keyword"
        assert settings.test_timeout == "10 seconds"
        assert settings.force_tags == ["force-a", "force-b"]
        assert settings.default_tags == ["default-a", "default-b"]

    def test_parse_variables_scalar(self):
        result = RobotFrameworkParser().parse_file(FIXTURES / "variables.robot")

        scalar = result.suite.variables[0]
        assert scalar.name == "${SCALAR}"
        assert scalar.kind == "scalar"
        assert scalar.value == "value"

    def test_parse_variables_list_dict(self):
        result = RobotFrameworkParser().parse_file(FIXTURES / "variables.robot")
        variables = {item.name: item for item in result.suite.variables}

        assert variables["@{LIST}"].kind == "list"
        assert variables["@{LIST}"].value == ["a", "b"]
        assert variables["&{DICT}"].kind == "dict"
        assert variables["&{DICT}"].value == {"key": "value", "other": "item"}

    def test_parse_imports(self):
        result = RobotFrameworkParser().parse_file(FIXTURES / "basic_suite.robot")
        imports = result.suite.imports

        assert [(item.type, item.name, item.alias) for item in imports] == [
            ("library", "Collections", "Col"),
            ("resource", "resource.robot", None),
            ("variables", "variables.py", None),
        ]
        assert imports[2].args == ["prod"]

    def test_parse_test_case(self):
        result = RobotFrameworkParser().parse_file(FIXTURES / "basic_suite.robot")

        test_case = result.suite.test_cases[0]
        assert test_case.name == "My Test"
        assert test_case.doc == "A simple test"
        assert test_case.tags == ["critical"]
        assert [step.keyword for step in test_case.body] == ["Log", "My Keyword"]

    def test_parse_keyword(self):
        result = RobotFrameworkParser().parse_file(FIXTURES / "keywords.robot")

        keyword = result.suite.keywords[0]
        assert keyword.name == "Keyword With Args"
        assert keyword.doc == "Keyword docs"
        assert [(arg.name, arg.default, arg.kind) for arg in keyword.args] == [
            ("${required}", None, "positional"),
            ("${optional}", "default", "optional"),
            ("@{items}", None, "varargs"),
            ("&{options}", None, "kwargs"),
        ]

    def test_parse_steps(self):
        result = RobotFrameworkParser().parse_file(FIXTURES / "basic_suite.robot")

        step = result.suite.keywords[0].body[0]
        assert step.keyword == "Log"
        assert step.args == ["${arg}"]
        assert step.assign == []

    def test_parse_var_syntax_variables(self):
        result = RobotFrameworkParser().parse_text(
            "*** Test Cases ***\nT\n    VAR    ${value: int}    1    scope=TEST\n    Log    ${value}\n",
            source_name="var.robot",
        )

        variable = result.suite.test_cases[0].variables[0]
        assert variable.name == "${value}"
        assert variable.value == "1"
        assert variable.kind == "scalar"
        assert variable.scope == "test"
        assert variable.type_annotation == "int"

    def test_parse_group_body_keywords(self):
        result = RobotFrameworkParser().parse_text(
            "*** Test Cases ***\nT\n    GROUP    Setup\n        Log    inside\n    END\n",
            source_name="group.robot",
        )

        assert [step.keyword for step in result.suite.test_cases[0].body] == ["Log"]
        assert result.suite.test_cases[0].body[0].args == ["inside"]

    def test_parse_typed_secret_variable(self):
        result = RobotFrameworkParser().parse_text(
            "*** Variables ***\n${password: Secret}    value\n",
            source_name="secret.robot",
        )

        variable = result.suite.variables[0]
        assert variable.name == "${password}"
        assert variable.kind == "secret"
        assert variable.type_annotation == "Secret"

    def test_parse_keyword_argument_type_annotation(self):
        result = RobotFrameworkParser().parse_text(
            "*** Keywords ***\nK\n    [Arguments]    ${count: int}\n    Log    ${count}\n",
            source_name="typed_arg.robot",
        )

        arg = result.suite.keywords[0].args[0]
        assert arg.name == "${count}"
        assert arg.type_annotation == "int"

    def test_parse_text(self):
        result = RobotFrameworkParser().parse_text(
            "*** Test Cases ***\nInline\n    Log    ok\n",
            source_name="inline.robot",
        )

        assert result.suite.name == "inline"
        assert result.suite.test_cases[0].name == "Inline"

    def test_parse_with_syntax_error(self):
        result = RobotFrameworkParser().parse_file(FIXTURES / "syntax_error.robot")

        assert result.suite is not None
        assert len(result.errors) == 1
        assert result.errors[0].severity == "error"
        assert result.errors[0].code == "parse_error"

    def test_adapter_no_direct_rf_import_in_core(self):
        src = Path(__file__).parents[3] / "src" / "robot_lsp"
        forbidden = []
        for folder in ["domain", "application", "protocol"]:
            for path in (src / folder).rglob("*.py"):
                text = path.read_text(encoding="utf-8")
                if "robot.api.parsing" in text or "robot.parsing" in text:
                    forbidden.append(str(path.relative_to(src)))

        assert forbidden == []
