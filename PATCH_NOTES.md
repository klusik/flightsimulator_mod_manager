# Patch Notes

## Version 0.1.0

Version 0.1.0 is the first public-ready build of Flight Simulator Mod Manager. It provides a focused Windows desktop interface for reviewing Microsoft Flight Simulator 2024 Community packages and safely enabling or disabling them by moving complete package directories between the active Community folder and a configurable disabled-packages folder.

### Highlights

#### Safe package enable and disable workflow

- Added Community-folder autodetection with manual folder selection when detection is unavailable or the user prefers another installation.
- Added a suggested disabled-packages location next to Community, such as `C:\something\Community_disabled`, while allowing the user to configure another same-volume location.
- Added batch enable and disable actions that move complete package directories without editing their contents.
- Added confirmation before filesystem changes and clear per-package operation results.
- Rejected destination conflicts, directory merges, overwrites, deletions, symbolic links, junctions, cross-volume moves, nested roots, and application directories inside either managed root.
- Revalidated package paths and required metadata immediately before every move.

#### Package discovery and organization

- Added scanning of direct child directories containing root-level `manifest.json` and `layout.json` files.
- Added display of package title, version, creator, directory name, and enabled, disabled, conflicted, or invalid state.
- Added case-insensitive name search across display names and package-directory names.
- Added status filters for all, enabled, disabled, conflicted, and invalid packages.
- Added sortable table headings with deterministic directory-name tie breaking.
- Added Select all, Clear, `Ctrl+A`, `Escape`, and `F5` controls for efficient package management.
- Added horizontal and vertical scrollbars and redundant state symbols, text, and colors for faster recognition.

#### Windows distribution

- Added a self-contained windowed executable build through `build.bat` and PyInstaller.
- Added a per-user Windows installer through `installer.bat` and Inno Setup 7, with Inno Setup 6 compatibility.
- Added Windows Installed apps registration, Start Menu integration, an optional desktop shortcut, and uninstall support.
- Added a source deployment archive through `deploy.bat` for inspection and alternative distribution.

### Technical Details

#### Application architecture

- Added a strictly typed Model-View-Controller application under `src/fs24_mod_manager`.
- Added immutable package models and replaceable application state, with JSON used only for user preferences.
- Added focused services for Community discovery, root validation, package scanning, package movement, and settings persistence.
- Kept all Tkinter widget access on the main thread while a single background worker serializes scans and move batches.
- Added scan generations so results produced for obsolete path selections cannot replace current state.
- Set Python 3.13 as the minimum supported version while allowing newer Python 3 releases.
- Avoided `from __future__ import annotations` throughout the project.

#### Persistence and compatibility

- Added versioned settings storage under `%LOCALAPPDATA%\FS24ModManager`.
- Added validation and safe fallback behavior for malformed, incompatible, or incorrectly typed settings data.
- Kept the filesystem authoritative for package state; no database, package registry, links, or simulator-file modifications are used.
- Limited Version 0.1.0 to Windows and Microsoft Flight Simulator 2024 directory-package workflows.

#### Quality and release tooling

- Added Ruff formatting and linting, strict mypy checks, and pytest coverage for scanner, mover, settings, and project contracts.
- Added a Windows GitHub Actions quality workflow for the supported Python range.
- Added isolated build environments and cleanup so generated PyInstaller work files are not left in the repository.
- Added source archive and installer definitions whose generated artifacts remain outside normal Git tracking.

### Tests

#### Automated coverage

- Covered valid, conflicted, and invalid package discovery using temporary synthetic directories.
- Covered safe directory moves and refusal of destination conflicts.
- Covered settings round trips and recovery from invalid JSON.
- Qualified Version 0.1.0 with Ruff, strict mypy, pytest, a hidden-window Tkinter startup smoke test, executable packaging, source archive inspection, and installer compilation.

### User Impact

#### For players

- Community packages can be temporarily disabled without deleting them or modifying their contents.
- Disabled packages remain ordinary directories in a user-selected folder and can be restored through the same interface.
- Search, status filtering, sorting, and bulk selection make larger Community folders easier to manage.
- Flight Simulator should be closed before enabling or disabling packages.

#### Distribution notes

- The application and installer are currently unsigned, so Windows may show a reputation or publisher warning.
- No project license has been selected yet. The repository owner must choose one before public distribution or reuse is authorized.
