"""Verify all modules can be imported without errors."""

import importlib
import pkgutil

import robot_lsp


def _iter_modules(package):
    modules = []
    for importer, modname, ispkg in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        modules.append(modname)
        if ispkg:
            sub_package = importlib.import_module(modname)
            modules.extend(_iter_modules(sub_package))
    return modules


class TestImports:
    def test_all_modules_import(self):
        errors = []
        for modname in _iter_modules(robot_lsp):
            try:
                importlib.import_module(modname)
            except Exception as exc:
                errors.append(f"{modname}: {exc}")
        assert not errors, f"Import errors:\n" + "\n".join(errors)
