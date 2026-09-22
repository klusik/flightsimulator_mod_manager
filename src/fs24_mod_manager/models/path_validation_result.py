"""Path validation result model."""

from dataclasses import dataclass

from fs24_mod_manager.models.error_code import ErrorCode


@dataclass(frozen=True, slots=True)
class PathValidationResult:
    """Report whether configured roots are safe to use."""

    valid: bool
    message: str = ""
    error_code: ErrorCode | None = None
