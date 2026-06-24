from __future__ import annotations

import re

from robot.version import VERSION

from robot_lsp.domain.features import FeatureSet, VersionInfo


class UnsupportedRobotFrameworkVersionError(RuntimeError):
    pass


class RobotFrameworkVersionDetector:
    def detect(self) -> FeatureSet:
        version = parse_version(VERSION)
        if not version.at_least(7, 0):
            raise UnsupportedRobotFrameworkVersionError(
                f"Robot Framework >= 7.0 is required, got {VERSION}"
            )
        return FeatureSet(
            version=version,
            has_group=_has_group(version),
            has_secret_variables=version.at_least(7, 4),
        )


def parse_version(version: str) -> VersionInfo:
    parts = [int(match) for match in re.findall(r"\d+", version)[:3]]
    while len(parts) < 3:
        parts.append(0)
    return VersionInfo(major=parts[0], minor=parts[1], patch=parts[2])


def _has_group(version: VersionInfo) -> bool:
    if version.at_least(7, 2):
        return True
    try:
        from robot.api.parsing import Group  # noqa: F401
    except ImportError:
        return False
    return True
