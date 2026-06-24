import pytest

from robot_lsp.domain.features import VersionInfo
from robot_lsp.infrastructure.robotframework.version import (
    RobotFrameworkVersionDetector,
    UnsupportedRobotFrameworkVersionError,
    parse_version,
)


class TestRobotFrameworkVersion:
    def test_version_detection(self):
        features = RobotFrameworkVersionDetector().detect()

        assert features.version.at_least(7, 0)
        assert isinstance(features.has_group, bool)
        assert isinstance(features.has_secret_variables, bool)

    def test_feature_set_rf7(self):
        assert parse_version("7.4.2") == VersionInfo(major=7, minor=4, patch=2)
        assert parse_version("7.0") == VersionInfo(major=7, minor=0, patch=0)

    def test_unsupported_version_error_is_available(self):
        with pytest.raises(UnsupportedRobotFrameworkVersionError):
            raise UnsupportedRobotFrameworkVersionError("unsupported")
