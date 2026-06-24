from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VersionInfo:
    major: int
    minor: int
    patch: int

    def at_least(self, major: int, minor: int = 0) -> bool:
        return (self.major, self.minor) >= (major, minor)


@dataclass(frozen=True)
class FeatureSet:
    version: VersionInfo
    has_group: bool
    has_secret_variables: bool
