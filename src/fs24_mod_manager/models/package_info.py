"""Package metadata model."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class PackageStatus(StrEnum):
    """Describe where and whether a package can be managed."""

    ENABLED = "Enabled"
    DISABLED = "Disabled"
    CONFLICTED = "Conflicted"
    INVALID = "Invalid"


@dataclass(frozen=True, slots=True)
class PackageInfo:
    """Describe one package found in a configured root."""

    directory_name: str
    path: Path
    title: str
    version: str
    creator: str
    manufacturer: str
    status: PackageStatus
    diagnostic: str = ""

    @property
    def identity(self) -> str:
        """Return the case-insensitive stable package identity.

        @return: Normalized directory identity.
        """
        return self.directory_name.casefold()
