"""Persisted user preferences."""

from dataclasses import dataclass
from pathlib import Path

from fs24_mod_manager.config import Config


@dataclass(slots=True)
class UserSettings:
    """Hold user-selected paths and window preferences."""

    community_path: Path | None = None
    disabled_path: Path | None = None
    window_geometry: str = Config.DEFAULT_GEOMETRY
    settings_version: int = Config.SETTINGS_VERSION
