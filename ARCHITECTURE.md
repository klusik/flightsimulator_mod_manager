# Architecture

## Overview

Flight Simulator Mod Manager is a Python 3.13+ Windows desktop application using Tkinter and a strict Model-View-Controller structure. The filesystem is the authoritative package state; JSON persists only user preferences.

```text
__main__.py
    -> App composition root
        -> Config and SettingsStore
        -> typed models
        -> filesystem services
        -> MainView
        -> MainController
            -> one background worker
            -> thread-safe completion queue
            -> Tk main thread
```

## Dependency rules

- `models` contain typed dataclasses and enums. They do not import Tkinter or services.
- `services` perform discovery, scanning, validation, settings persistence, and package moves. They do not import Tkinter.
- `views` own widgets, presentation formatting, filtering, selection, and dialogs. They do not access the filesystem directly.
- `controllers` translate user intent into model/service operations and send completed state to the view.
- `app.py` is the only composition root and constructs concrete collaborators.
- Dependencies point inward toward models; services and views do not depend on each other.

## Runtime state

`AppState` holds the current replaceable snapshot: settings, packages, scan generation, busy state, and operation results. `PackageInfo` is immutable so scan results can safely cross the worker boundary. The package directory name, normalized with `casefold()`, is the stable identity.

The controller uses a single-worker `ThreadPoolExecutor`. Scans and move batches run sequentially. Worker completion callbacks put callables into a thread-safe queue; only the Tk main thread drains that queue and touches widgets. A scan generation prevents stale results from replacing newer path state.

## Filesystem safety boundary

Only direct children of the configured roots qualify as packages. A package requires root-level `manifest.json` and `layout.json`. Scans do not recurse or follow symbolic links. Every move revalidates roots, source ownership, metadata, destination absence, same-volume placement, and application-directory exclusion immediately before mutation. Successful moves are verified on disk before being reported.

## User interface structure

The main window contains:

1. A title and live package summary.
2. Read-only Community and disabled-root paths with browse actions.
3. Name search, package-state filtering, selection, and refresh controls.
4. A vertically and horizontally scrollable package table.
5. Selection-aware enable/disable actions and a status line.

Package state is communicated redundantly by symbol, text, and color:

| Symbol | State |
| --- | --- |
| `●` | Enabled |
| `○` | Disabled |
| `⚠` | Conflicted |
| `✕` | Invalid |

Keyboard controls are `Ctrl+A` for all visible rows, `Escape` to clear selection, and `F5` to refresh.

The view performs presentation-only filtering and ordering over the current immutable package snapshot. Name search matches the display title and package-directory name. The state selector filters enabled, disabled, conflicted, or invalid packages. Clicking a heading selects its case-insensitive ordering and a second click reverses it; the directory name is the deterministic tie breaker.

## Persistence and packaging

Settings are stored under `%LOCALAPPDATA%\FS24ModManager` through temporary-file replacement. `build.bat` creates a single PyInstaller executable in `dist`; `deploy.bat` creates the source ZIP. `installer.bat` rebuilds the executable and compiles `packaging/installer.iss` with Inno Setup, producing a per-user Windows installer with Start Menu registration and uninstall support. Generated artifacts remain ignored by Git and are intended for GitHub Release assets.

## Verification

Ruff enforces formatting and linting, mypy runs in strict mode against the Python 3.13 compatibility floor, and pytest uses only temporary synthetic package directories. Tests must never mutate a real Flight Simulator installation.
