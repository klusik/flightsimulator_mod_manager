"""Configured-root safety validation."""

import os
from pathlib import Path

from fs24_mod_manager.models.error_code import ErrorCode
from fs24_mod_manager.models.path_validation_result import PathValidationResult


class PathValidator:
    """Validate Community and disabled roots before filesystem work."""

    def validate_roots(self, community: Path, disabled: Path) -> PathValidationResult:
        """Validate a pair of package roots.

        @param community: Active Community directory.
        @param disabled: Disabled-package directory.
        @return: Structured validation outcome.
        """
        active = community.resolve(strict=False)
        archive = disabled.resolve(strict=False)
        if not active.is_dir():
            return PathValidationResult(
                False, "Community directory does not exist.", ErrorCode.SOURCE_MISSING
            )
        if active == archive or active in archive.parents or archive in active.parents:
            return PathValidationResult(
                False, "Package roots cannot be identical or nested.", ErrorCode.PACKAGE_CONFLICT
            )
        if self._volume(active) != self._volume(archive):
            return PathValidationResult(
                False, "Both roots must be on the same volume.", ErrorCode.CROSS_VOLUME
            )
        if not os.access(active, os.R_OK | os.W_OK):
            return PathValidationResult(
                False, "Community directory is not writable.", ErrorCode.PATH_NOT_WRITABLE
            )
        parent = archive if archive.exists() else archive.parent
        if not parent.is_dir() or not os.access(parent, os.W_OK):
            return PathValidationResult(
                False,
                "Disabled directory cannot be created or written.",
                ErrorCode.PATH_NOT_WRITABLE,
            )
        return PathValidationResult(True)

    def is_direct_child(self, child: Path, root: Path) -> bool:
        """Check a resolved direct-child relationship.

        @param child: Candidate package directory.
        @param root: Expected package root.
        @return: Whether the path is a direct child.
        """
        return child.resolve(strict=False).parent == root.resolve(strict=False)

    def _volume(self, path: Path) -> str:
        """Return a normalized filesystem volume identifier.

        @param path: Path to inspect.
        @return: Case-insensitive drive or anchor.
        """
        return (path.drive or path.anchor).casefold()
