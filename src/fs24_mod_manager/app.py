"""Application composition root."""

import tkinter as tk
from pathlib import Path

from fs24_mod_manager.config import Config
from fs24_mod_manager.controllers.main_controller import MainController
from fs24_mod_manager.models.app_state import AppState
from fs24_mod_manager.services.community_locator import CommunityLocator
from fs24_mod_manager.services.package_mover import PackageMover
from fs24_mod_manager.services.package_scanner import PackageScanner
from fs24_mod_manager.services.path_validator import PathValidator
from fs24_mod_manager.services.settings_store import SettingsStore
from fs24_mod_manager.views.main_view import MainView


class App:
    """Own and run the fully composed desktop application."""

    def __init__(self, application_directory: Path | None = None) -> None:
        """Compose application collaborators.

        @param application_directory: Runtime directory excluded from packages.
        """
        runtime = (application_directory or Path.cwd()).resolve()
        data = Config.application_data_directory()
        store = SettingsStore(data / Config.SETTINGS_FILENAME)
        state = AppState(store.load())
        root = tk.Tk()
        root.geometry(state.settings.window_geometry)
        view = MainView(root)
        validator = PathValidator()
        self._root = root
        self._controller = MainController(
            view,
            state,
            store,
            CommunityLocator(),
            validator,
            PackageScanner(runtime),
            PackageMover(validator, runtime),
        )

    def run(self) -> None:
        """Start discovery and the Tk event loop."""
        self._controller.start()
        self._root.mainloop()
