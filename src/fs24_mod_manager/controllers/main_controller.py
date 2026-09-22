"""Main MVC controller."""

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from queue import Empty, Queue

from fs24_mod_manager.models.app_state import AppState
from fs24_mod_manager.models.operation_result import PackageAction
from fs24_mod_manager.models.package_info import PackageInfo, PackageStatus
from fs24_mod_manager.services.community_locator import CommunityLocator
from fs24_mod_manager.services.package_mover import PackageMover
from fs24_mod_manager.services.package_scanner import PackageScanner
from fs24_mod_manager.services.path_validator import PathValidator
from fs24_mod_manager.services.settings_store import SettingsStore
from fs24_mod_manager.views.main_view import MainView


class MainController:
    """Coordinate UI intent and single-worker filesystem operations."""

    def __init__(
        self,
        view: MainView,
        state: AppState,
        store: SettingsStore,
        locator: CommunityLocator,
        validator: PathValidator,
        scanner: PackageScanner,
        mover: PackageMover,
    ) -> None:
        """Create and connect the controller.

        @param view: Main application view.
        @param state: Mutable in-memory state.
        @param store: Settings persistence.
        @param locator: Community discovery service.
        @param validator: Root validator.
        @param scanner: Package scanner.
        @param mover: Package mover.
        """
        self._view, self._state, self._store = view, state, store
        self._locator, self._validator, self._scanner, self._mover = (
            locator,
            validator,
            scanner,
            mover,
        )
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="fs24-worker")
        self._events: Queue[Callable[[], None]] = Queue()
        self._closed = False
        view.bind_actions(
            self.choose_community,
            self.choose_disabled,
            self.refresh,
            self.enable,
            self.disable,
            self.close,
        )
        view.root.after(100, self._poll_events)

    def start(self) -> None:
        """Discover initial paths and start the first scan."""
        settings = self._state.settings
        candidates = self._locator.discover(settings.community_path)
        if settings.community_path is None and len(candidates) == 1:
            settings.community_path = candidates[0]
        if settings.community_path and settings.disabled_path is None:
            settings.disabled_path = self._locator.suggested_disabled_path(settings.community_path)
        self._sync_paths()
        if settings.community_path and settings.disabled_path:
            self.refresh()

    def choose_community(self) -> None:
        """Select and validate a Community root."""
        selected = self._view.choose_directory(self._state.settings.community_path)
        if selected:
            self._state.settings.community_path = selected.resolve()
            self._state.settings.disabled_path = self._locator.suggested_disabled_path(
                selected.resolve()
            )
            self._save_and_refresh()

    def choose_disabled(self) -> None:
        """Select and validate a disabled root."""
        selected = self._view.choose_directory(self._state.settings.disabled_path)
        if selected:
            self._state.settings.disabled_path = selected.resolve()
            self._save_and_refresh()

    def refresh(self) -> None:
        """Start a background scan when configured roots are safe."""
        roots = self._roots()
        if roots is None or self._state.busy:
            return
        community, disabled = roots
        validation = self._validator.validate_roots(community, disabled)
        if not validation.valid:
            self._view.show_error(validation.message)
            return
        self._state.scan_generation += 1
        generation = self._state.scan_generation
        self._set_busy(True, "Scanning packages…")
        future = self._executor.submit(self._scanner.scan, community, disabled)
        future.add_done_callback(
            lambda completed: self._events.put(lambda: self._finish_scan(generation, completed))
        )

    def enable(self) -> None:
        """Request enabling selected disabled packages."""
        self._move_selected(PackageAction.ENABLE)

    def disable(self) -> None:
        """Request disabling selected enabled packages."""
        self._move_selected(PackageAction.DISABLE)

    def close(self) -> None:
        """Close only when no mutating operation is active."""
        if self._state.busy:
            self._view.show_error("Please wait for the current operation to finish.")
            return
        self._state.settings.window_geometry = self._view.root.geometry()
        self._store.save(self._state.settings)
        self._executor.shutdown(wait=False, cancel_futures=True)
        self._closed = True
        self._view.root.destroy()

    def _move_selected(self, action: PackageAction) -> None:
        """Validate and start a selected batch.

        @param action: Requested direction.
        """
        roots = self._roots()
        expected = (
            PackageStatus.DISABLED if action is PackageAction.ENABLE else PackageStatus.ENABLED
        )
        selected = [item for item in self._view.selected_packages() if item.status is expected]
        if roots is None or not selected or self._state.busy:
            return
        if not self._view.confirm(
            action.value.title(),
            f"{action.value.title()} {len(selected)} selected package(s)?\n"
            "Close Flight Simulator before continuing.",
        ):
            return
        community, disabled = roots
        self._set_busy(True, f"{action.value.title()} operation running…")
        future = self._executor.submit(self._move_batch, selected, community, disabled)
        future.add_done_callback(
            lambda completed: self._events.put(lambda: self._finish_move(completed))
        )

    def _poll_events(self) -> None:
        """Drain worker completions exclusively on the Tk thread."""
        try:
            while True:
                self._events.get_nowait()()
        except Empty:
            pass
        if not self._closed:
            self._view.root.after(100, self._poll_events)

    def _move_batch(
        self, packages: list[PackageInfo], community: Path, disabled: Path
    ) -> list[str]:
        """Move a batch sequentially on the worker.

        @param packages: Packages to move.
        @param community: Enabled root.
        @param disabled: Disabled root.
        @return: User-facing result messages.
        """
        results = [self._mover.move(item, community, disabled) for item in packages]
        self._state.latest_results = results
        return [result.message for result in results]

    def _finish_scan(self, generation: int, future: Future[list[PackageInfo]]) -> None:
        """Apply a current worker scan result.

        @param generation: Scan generation.
        @param future: Completed scan.
        """
        try:
            if generation == self._state.scan_generation:
                self._state.packages = future.result()
                self._view.show_packages(self._state.packages)
                self._view.status_var.set(f"{len(self._state.packages)} packages")
        except Exception as error:
            self._view.show_error(f"Package scan failed: {error}")
        finally:
            self._set_busy(False, self._view.status_var.get())

    def _finish_move(self, future: Future[list[str]]) -> None:
        """Report a completed batch and rescan.

        @param future: Completed batch.
        """
        try:
            messages = future.result()
            self._view.status_var.set("; ".join(messages))
        except Exception as error:
            self._view.show_error(f"Package operation failed: {error}")
        finally:
            self._state.busy = False
            self._view.set_busy(False)
            self.refresh()

    def _save_and_refresh(self) -> None:
        """Persist path changes and replace visible state."""
        self._state.packages.clear()
        self._state.scan_generation += 1
        self._view.show_packages([])
        self._sync_paths()
        self._store.save(self._state.settings)
        self.refresh()

    def _sync_paths(self) -> None:
        """Copy configured paths into display variables."""
        self._view.community_var.set(str(self._state.settings.community_path or ""))
        self._view.disabled_var.set(str(self._state.settings.disabled_path or ""))

    def _roots(self) -> tuple[Path, Path] | None:
        """Return configured roots.

        @return: Root pair or `None`.
        """
        settings = self._state.settings
        if settings.community_path is None or settings.disabled_path is None:
            self._view.show_error("Choose the Community and disabled directories first.")
            return None
        return settings.community_path, settings.disabled_path

    def _set_busy(self, busy: bool, message: str) -> None:
        """Synchronize busy state and view.

        @param busy: New state.
        @param message: Status text.
        """
        self._state.busy = busy
        self._view.set_busy(busy)
        self._view.status_var.set(message)
