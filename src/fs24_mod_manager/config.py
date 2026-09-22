"""Application configuration defaults."""

from pathlib import Path


class Config:
    """Provide immutable application-wide defaults."""

    APP_NAME: str = "Flight Simulator Mod Manager"
    APP_VERSION: str = "0.1.0"
    APP_DIRECTORY: str = "FS24ModManager"
    SETTINGS_VERSION: int = 1
    SETTINGS_FILENAME: str = "settings.json"
    LOG_FILENAME: str = "application.log"
    DISABLED_SUFFIX: str = "_disabled"
    DEFAULT_GEOMETRY: str = "1100x680"
    LOG_MAX_BYTES: int = 1_000_000
    LOG_BACKUP_COUNT: int = 3

    @classmethod
    def application_data_directory(cls) -> Path:
        """Return the per-user application data directory.

        @return: Local application data directory for this program.
        """
        import os

        base = os.environ.get("LOCALAPPDATA")
        return Path(base) / cls.APP_DIRECTORY if base else Path.home() / f".{cls.APP_DIRECTORY}"
