"""Stable operation error codes."""

from enum import StrEnum


class ErrorCode(StrEnum):
    """Identify failures independently from presentation text."""

    SOURCE_MISSING = "source_missing"
    DESTINATION_EXISTS = "destination_exists"
    PATH_NOT_WRITABLE = "path_not_writable"
    CROSS_VOLUME = "cross_volume"
    PACKAGE_INVALID = "package_invalid"
    PACKAGE_CONFLICT = "package_conflict"
    ACCESS_DENIED = "access_denied"
    FILE_LOCKED = "file_locked"
    OPERATION_CANCELLED = "operation_cancelled"
    UNEXPECTED_ERROR = "unexpected_error"
