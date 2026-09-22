"""Versioned JSON settings persistence."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from fs24_mod_manager.config import Config
from fs24_mod_manager.models.user_settings import UserSettings


class SettingsStore:
    """Load and atomically save validated user preferences."""

    def __init__(self, path: Path) -> None:
        """Create a settings store.

        @param path: JSON settings location.
        """
        self._path = path

    def load(self) -> UserSettings:
        """Load settings or recover safely from invalid content.

        @return: Loaded settings or defaults.
        """
        if not self._path.exists():
            return UserSettings()
        try:
            data: Any = json.loads(self._path.read_text(encoding="utf-8"))
            if (
                not isinstance(data, dict)
                or data.get("settings_version") != Config.SETTINGS_VERSION
            ):
                raise ValueError("Unsupported settings document.")
            geometry_value = data.get("window_geometry")
            geometry = (
                geometry_value if isinstance(geometry_value, str) else Config.DEFAULT_GEOMETRY
            )
            return UserSettings(
                self._optional_path(data.get("community_path")),
                self._optional_path(data.get("disabled_path")),
                geometry,
            )
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            self._preserve_invalid()
            return UserSettings()

    def save(self, settings: UserSettings) -> None:
        """Atomically persist settings.

        @param settings: Preferences to serialize.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._path.with_suffix(".tmp")
        data = {
            "settings_version": Config.SETTINGS_VERSION,
            "community_path": str(settings.community_path) if settings.community_path else None,
            "disabled_path": str(settings.disabled_path) if settings.disabled_path else None,
            "window_geometry": settings.window_geometry,
        }
        temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(temporary, self._path)

    def _optional_path(self, value: object) -> Path | None:
        """Convert a valid optional string path.

        @param value: Untrusted JSON value.
        @return: Path or `None`.
        """
        return Path(value) if isinstance(value, str) and value else None

    def _preserve_invalid(self) -> None:
        """Rename an invalid settings document when possible."""
        try:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            self._path.replace(self._path.with_name(f"{self._path.stem}.{stamp}.invalid.json"))
        except OSError:
            return
