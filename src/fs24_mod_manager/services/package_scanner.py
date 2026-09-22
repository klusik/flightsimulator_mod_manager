"""Direct-child package discovery."""

import json
import os
from pathlib import Path
from typing import Any

from fs24_mod_manager.models.package_info import PackageInfo, PackageStatus


class PackageScanner:
    """Scan configured roots without following links or recursing."""

    def __init__(self, application_directory: Path) -> None:
        """Create a scanner.

        @param application_directory: Directory that must never be managed.
        """
        self._application_directory = application_directory.resolve(strict=False)

    def scan(self, community: Path, disabled: Path) -> list[PackageInfo]:
        """Scan both roots and mark case-insensitive conflicts.

        @param community: Enabled package root.
        @param disabled: Disabled package root.
        @return: Sorted package snapshot.
        """
        packages = self._scan_root(community, PackageStatus.ENABLED)
        packages.extend(self._scan_root(disabled, PackageStatus.DISABLED))
        counts: dict[str, int] = {}
        for package in packages:
            counts[package.identity] = counts.get(package.identity, 0) + 1
        resolved = [
            self._with_status(item, PackageStatus.CONFLICTED, "Duplicate package identity.")
            if counts[item.identity] > 1
            else item
            for item in packages
        ]
        return sorted(
            resolved, key=lambda item: (item.title.casefold(), item.directory_name.casefold())
        )

    def _scan_root(self, root: Path, status: PackageStatus) -> list[PackageInfo]:
        """Scan valid direct children of one root.

        @param root: Root to enumerate.
        @param status: State assigned to discovered packages.
        @return: Package descriptions.
        """
        if not root.is_dir():
            return []
        found: list[PackageInfo] = []
        with os.scandir(root) as entries:
            for entry in entries:
                path = Path(entry.path)
                if not entry.is_dir(follow_symlinks=False) or entry.is_symlink():
                    continue
                if path.resolve(strict=False) == self._application_directory:
                    continue
                manifest = self._case_insensitive_file(path, "manifest.json")
                layout = self._case_insensitive_file(path, "layout.json")
                if manifest is None or layout is None:
                    continue
                found.append(self._read_package(path, manifest, status))
        return found

    def _read_package(self, path: Path, manifest: Path, status: PackageStatus) -> PackageInfo:
        """Read display metadata without allowing malformed JSON to escape.

        @param path: Package directory.
        @param manifest: Root manifest file.
        @param status: Package state.
        @return: Parsed or invalid package description.
        """
        try:
            data: Any = json.loads(manifest.read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict):
                raise ValueError("Manifest root is not an object.")
            return PackageInfo(
                path.name,
                path,
                self._text(data.get("title"), path.name),
                self._text(data.get("package_version"), ""),
                self._text(data.get("creator"), ""),
                self._text(data.get("manufacturer"), ""),
                status,
            )
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            return PackageInfo(
                path.name, path, path.name, "", "", "", PackageStatus.INVALID, str(error)
            )

    def _case_insensitive_file(self, root: Path, expected: str) -> Path | None:
        """Find a direct file using Windows-style case comparison.

        @param root: Directory to inspect.
        @param expected: Expected file name.
        @return: Matching path or `None`.
        """
        for item in root.iterdir():
            if item.name.casefold() == expected.casefold() and item.is_file():
                return item
        return None

    def _text(self, value: object, fallback: str) -> str:
        """Normalize an optional manifest value.

        @param value: Untrusted JSON value.
        @param fallback: Value used for non-text input.
        @return: Normalized text.
        """
        return value.strip() if isinstance(value, str) and value.strip() else fallback

    def _with_status(
        self, package: PackageInfo, status: PackageStatus, diagnostic: str
    ) -> PackageInfo:
        """Copy a package with conflict state.

        @param package: Existing package model.
        @param status: Replacement state.
        @param diagnostic: Replacement diagnostic.
        @return: Updated immutable package.
        """
        return PackageInfo(
            package.directory_name,
            package.path,
            package.title,
            package.version,
            package.creator,
            package.manufacturer,
            status,
            diagnostic,
        )
