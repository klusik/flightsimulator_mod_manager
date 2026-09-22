"""Verified same-volume package moves."""

import shutil
import uuid
from pathlib import Path

from fs24_mod_manager.models.error_code import ErrorCode
from fs24_mod_manager.models.operation_result import OperationResult, PackageAction
from fs24_mod_manager.models.package_info import PackageInfo, PackageStatus
from fs24_mod_manager.services.path_validator import PathValidator


class PackageMover:
    """Move complete packages after revalidating every safety condition."""

    def __init__(self, validator: PathValidator, application_directory: Path) -> None:
        """Create a mover.

        @param validator: Root and relationship validator.
        @param application_directory: Directory that cannot be moved.
        """
        self._validator = validator
        self._application_directory = application_directory.resolve(strict=False)

    def move(self, package: PackageInfo, community: Path, disabled: Path) -> OperationResult:
        """Move one package to its opposite configured root.

        @param package: Freshly selected package model.
        @param community: Enabled root.
        @param disabled: Disabled root.
        @return: Verified structured outcome.
        """
        action = (
            PackageAction.DISABLE
            if package.status is PackageStatus.ENABLED
            else PackageAction.ENABLE
        )
        source_root = community if action is PackageAction.DISABLE else disabled
        target_root = disabled if action is PackageAction.DISABLE else community
        source = package.path.resolve(strict=False)
        destination = target_root.resolve(strict=False) / source.name
        operation_id = uuid.uuid4().hex
        failure = self._preflight(package, source, destination, source_root, community, disabled)
        if failure:
            code, message = failure
            return OperationResult(
                operation_id, package.identity, action, False, source, destination, message, code
            )
        try:
            target_root.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            valid = (
                not source.exists()
                and destination.is_dir()
                and (destination / "manifest.json").is_file()
                and (destination / "layout.json").is_file()
            )
            if not valid:
                return OperationResult(
                    operation_id,
                    package.identity,
                    action,
                    False,
                    source,
                    destination,
                    "Move completed but verification failed; inspect both paths.",
                    ErrorCode.UNEXPECTED_ERROR,
                )
            return OperationResult(
                operation_id,
                package.identity,
                action,
                True,
                source,
                destination,
                f"{package.title} moved successfully.",
            )
        except PermissionError as error:
            return OperationResult(
                operation_id,
                package.identity,
                action,
                False,
                source,
                destination,
                "Access was denied while moving the package.",
                ErrorCode.ACCESS_DENIED,
                str(error),
            )
        except OSError as error:
            return OperationResult(
                operation_id,
                package.identity,
                action,
                False,
                source,
                destination,
                "The package could not be moved.",
                ErrorCode.UNEXPECTED_ERROR,
                str(error),
            )

    def _preflight(
        self,
        package: PackageInfo,
        source: Path,
        destination: Path,
        source_root: Path,
        community: Path,
        disabled: Path,
    ) -> tuple[ErrorCode, str] | None:
        """Revalidate a requested move immediately before mutation.

        @param package: Package being moved.
        @param source: Resolved source.
        @param destination: Resolved destination.
        @param source_root: Expected source root.
        @param community: Enabled root.
        @param disabled: Disabled root.
        @return: Failure details or `None`.
        """
        roots = self._validator.validate_roots(community, disabled)
        if not roots.valid:
            return roots.error_code or ErrorCode.UNEXPECTED_ERROR, roots.message
        if package.status not in {PackageStatus.ENABLED, PackageStatus.DISABLED}:
            return ErrorCode.PACKAGE_CONFLICT, "Conflicted or invalid packages cannot be moved."
        if source == self._application_directory or not self._validator.is_direct_child(
            source, source_root
        ):
            return ErrorCode.PACKAGE_INVALID, "Package source is outside the expected root."
        if not source.is_dir():
            return ErrorCode.SOURCE_MISSING, "Package source no longer exists."
        if destination.exists():
            return ErrorCode.DESTINATION_EXISTS, "A destination with this name already exists."
        if not (source / "manifest.json").is_file() or not (source / "layout.json").is_file():
            return ErrorCode.PACKAGE_INVALID, "Package metadata is missing."
        return None
