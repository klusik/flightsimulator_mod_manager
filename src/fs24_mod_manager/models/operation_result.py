"""Package operation result model."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from fs24_mod_manager.models.error_code import ErrorCode


class PackageAction(StrEnum):
    """Identify a requested package state change."""

    ENABLE = "enable"
    DISABLE = "disable"


@dataclass(frozen=True, slots=True)
class OperationResult:
    """Describe the verified outcome of one package move."""

    operation_id: str
    package_identity: str
    action: PackageAction
    success: bool
    source: Path
    destination: Path
    message: str
    error_code: ErrorCode | None = None
    technical_details: str = ""
