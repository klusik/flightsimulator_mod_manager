# FS24 Community Mod Manager — Software Specification

> Living implementation contract. Update this document when an approved design decision changes.

## 1. Product goal

Build a small, dependable Windows desktop application in Python with Tkinter for Microsoft Flight Simulator 2024. The application lets a user see installed Community packages and enable or disable them by moving their package directories between the active `Community` directory and a disabled-mods directory.

The first version should remain deliberately simple. It does not need profiles, dependency resolution, downloads, cloud synchronization, symbolic links, junctions, a database, or background services.

## 2. Storage decision

### Recommended layout

Keep the disabled-mods directory **outside** the `Community` directory, preferably beside it and on the same drive:

```text
Packages/
├── Community/
│   ├── some-aircraft-mod/
│   └── some-scenery-mod/
├── Community_disabled/
│   └── another-aircraft-mod/
├── Official/
└── ...
```

The default disabled path should therefore be:

```text
<Community path>_disabled
```

For example, selecting `C:\something\Community` should preselect
`C:\something\Community_disabled`. This is only a suggested default: the user
can choose any safe directory outside `Community`.

Do not use `Community\_mod_archive` as the default. A leading underscore does not guarantee that Flight Simulator will ignore the directory. A container directory without its own manifest may be ignored as a package, but relying on the simulator never scanning manifests below it is an unnecessary risk. Keeping disabled packages completely outside `Community` is unambiguous.

Keeping both directories on the same filesystem also makes a directory move quick and normally atomic. The user must be able to select a different disabled directory, but the UI should warn when it is inside `Community` or on another volume.

### What “enabled” and “disabled” mean

- Enabled: the package directory is a direct child of the configured `Community` directory.
- Disabled: the complete package directory is a direct child of the configured disabled-mods directory.
- Enabling moves the entire directory from disabled storage to `Community`.
- Disabling moves the entire directory from `Community` to disabled storage.
- Files inside a package are never modified.
- The manager's own repository/application directory must never appear as a manageable mod.

## 3. Platform and technology

- Target: Windows, primarily Windows 10 and 11.
- Runtime: Python 3.13 or newer.
- GUI: standard-library Tkinter and `ttk`.
- File operations: `pathlib` and `shutil`/`os` as appropriate.
- Do not use `from __future__ import annotations` anywhere in the project.
- Use type annotations for every class attribute, method parameter, and return value. Use modern built-in generic syntax and types from `typing` where needed.
- Persistence: a small human-readable JSON settings file in the user's local application-data directory, not in `Community`.
- Logging: a rotating or size-limited text log in the same application-data directory.
- Packaging can be considered later; development starts as a normal Python application.

Prefer the standard library unless a dependency provides clear value. The initial version should not require administrator rights.

### Object-oriented and documentation rules

- The application must be object-oriented. Business behavior belongs to focused classes rather than collections of procedural module-level functions.
- Define one primary public class per Python module. Small supporting enums, typed aliases, protocols, exceptions, or immutable value objects may share the most closely related module when splitting them would reduce clarity.
- The composition/startup entry point may be a small module-level function. Do not create wrapper classes solely to satisfy an object-oriented rule.
- Configuration defaults must be typed attributes of the `Config` class rather than module-level constants; avoid mutable global state.
- Every class must have a useful class docstring describing its responsibility and collaborators.
- Every public and private method must have a docstring in the same project-wide format.
- Method docstrings must document each parameter with `@param <name>:` and document non-`None` results with `@return:`. Use `@raises <Exception>:` for expected exceptions.
- Docstrings should explain contracts and intent rather than repeat type hints line by line.
- All code must pass `mypy --strict` on Python 3.13 or newer.
- Use Ruff for linting and formatting, and `pytest` for automated tests.
- Keep classes cohesive and narrowly scoped. Modularity must not introduce abstract base classes, factories, or indirection that have no concrete use in this application.

Example method format:

```python
def find_packages(self, root: Path) -> list[PackageInfo]:
    """Find valid package directories directly beneath a root.

    @param root: Directory whose direct children will be inspected.
    @return: Package descriptions found beneath the supplied root.
    @raises PackageScanError: If the root cannot be read safely.
    """
```

## 4. Community directory discovery

Discovery should be helpful but never silently choose a doubtful directory.

Use this order:

1. Load the last user-confirmed Community path from settings and validate it.
2. Look for the simulator's `UserCfg.opt` in known Microsoft Store/Xbox and Steam locations.
3. Read `InstalledPackagesPath` from `UserCfg.opt`, then test `<InstalledPackagesPath>\Community`.
4. Test a short list of known default install locations.
5. If there is no single confident match, show a folder picker.

A valid Community directory is an existing directory named `Community`, or a user-selected directory that the user explicitly confirms. Discovery must handle quoted paths, spaces, custom package locations, inaccessible locations, and multiple installations.

The selected path must remain editable from the UI. Show the resolved full path prominently. Never create a guessed Community directory automatically.

For this development repository, the current directory's parent is likely the real Community directory. This may be offered as a development-time candidate, but it must not become a production assumption.

The finished application should normally be installed and run outside `Community`. Development from this repository is allowed, but the application must explicitly detect and exclude its own resolved directory from package results and move operations.

## 5. Package detection

Treat only **direct child directories** of each configured root as package candidates. Do not recursively combine nested packages.

A directory is a valid package when it contains both of these files at its root:

- `manifest.json`
- `layout.json`

File-name comparison should accommodate Windows case-insensitivity. Malformed JSON should not crash scanning; show the directory as invalid or unreadable with a diagnostic. Direct child folders without both files are not manageable mods and may optionally appear in a separate warning/status count.

Package directory identities and destination collisions must be compared case-insensitively, even if the underlying filesystem happens to permit case-sensitive names. If the same directory name exists in both roots, names differ only by case, or multiple manifests claim the same package identity, mark the entries as conflicted and do not move either package. Never guess which copy is authoritative.

From a valid manifest, display useful metadata when available:

- title or package name, with the directory name as fallback;
- version;
- creator/manufacturer if present;
- package directory name;
- enabled/disabled state.

Do not infer complex dependencies in version one.

## 6. Initial user interface

Use one main window with:

- configured Community path and a **Choose…** action;
- configured disabled-mods path and a **Choose…** action;
- a rescan/refresh action;
- a searchable table of packages;
- name search limited to mod display names and package-directory names;
- a state filter for all, enabled, disabled, conflicted, and invalid packages;
- clickable table headings for ascending and descending ordering with a visible direction marker;
- horizontal and vertical table scrollbars;
- columns for name, version, directory, and status;
- redundant state symbols, text, and color for quick recognition and accessibility;
- select-all and clear-selection actions that operate on currently visible filtered rows;
- **Enable** and **Disable** actions, disabled when they do not apply;
- a status line with package counts and the result of the latest operation;
- a compact error dialog for failed operations, with details recorded in the log.

Allow selecting multiple packages for a batch enable/disable operation. The interface should remain responsive; scanning and moves may run through a worker thread, but all Tkinter widget updates must occur on the main UI thread.

Before a batch move, show the action, package count, source, destination, and any conflicts that will be skipped, then require confirmation. A single-package confirmation may be configurable later; batch confirmation is mandatory in version one.

No visual redesign, tray icon, auto-updater, localization, or theme system is required for the first release.

## 7. File-operation rules

Safety is more important than convenience.

Before every move:

1. Resolve and normalize source and destination paths.
2. Confirm the source is a direct child of the expected configured root.
3. Confirm the destination is a direct child of the other configured root.
4. Reject the operation if source and destination roots are identical, nested inside one another, or resolve to an unsafe/broad location.
5. Reject the operation if a destination directory with the same name already exists. Never merge or overwrite packages automatically.
6. Reject attempts to move the running application/repository directory.
7. Ask the user to close Flight Simulator before moving packages. The app need not forcibly detect or terminate the simulator in version one.

Create the configured disabled-mods directory only after explicit user confirmation or the first disable action. Version one must reject cross-volume moves because they require a non-atomic copy-and-delete workflow. Explain the reason and ask the user to select disabled storage on the same volume as `Community`. On failure, report exactly which package failed and leave already completed independent moves recorded in the result; do not claim an all-or-nothing batch transaction.

Do not delete package directories. Do not edit manifests. Do not follow directory junctions or symbolic links during scans. A link itself should be skipped and reported to avoid moving data outside the selected roots unexpectedly.

## 8. Configuration and application data

Store only application preferences, for example:

```json
{
  "community_path": "D:\\...\\Packages\\Community",
  "disabled_path": "D:\\...\\Packages\\Community_disabled",
  "window_geometry": "1000x650"
}
```

Use an application-data location such as `%LOCALAPPDATA%\FS24ModManager`. Write settings safely through a temporary file followed by replacement so an interrupted save is unlikely to corrupt them.

Do not store absolute package inventories as authoritative state. The filesystem is the source of truth and is rescanned at startup and on request.

## 9. Architecture and suggested code boundaries

Use strict Model-View-Controller separation. Tkinter widgets must not scan directories, move packages, parse configuration, or contain business decisions. Models must not import Tkinter. Controllers coordinate user requests, model operations, and view updates.

### Model

The model represents configuration, packages, application state, validation, scanning, and move operations. Use typed `dataclass` value objects for live state. Current state must also have a JSON-serializable representation so it can be logged, inspected, tested, or persisted if later required. JSON is a serialization format, not the in-memory model itself.

The filesystem remains the authoritative source for installed package state. A JSON state document is a current snapshot/cache, not a database and not permission to move a package without revalidating its source and destination. The initial model should include at least:

- `Config`: central, typed configuration defaults and constants, including application name, default disabled-path suffix, settings/log filenames, and supported behavior defaults;
- `UserSettings`: the user's selected paths and UI preferences;
- `PackageInfo`: metadata and enabled/disabled state for one package;
- `AppState`: the current paths, package collection, scan status, and latest operation result;
- `OperationResult`: package, requested action, success flag, source, destination, stable error code, user-facing message, and optional technical details;
- `PathValidationResult`: typed validation outcome and any actionable diagnostics;
- focused scanner and mover classes that update or return model data safely.

`Config` must be the single source for defaults. Do not scatter configuration literals throughout controllers or views. Environment-specific and user-selected values belong in `UserSettings`, not as mutable global state in `Config`.

Services must return structured result objects or raise documented domain exceptions; they must not return UI-ready prose or ambiguous bare booleans. A multi-package operation returns one `OperationResult` per requested package so partial completion can be displayed and logged accurately.

### View

The view owns Tkinter widgets, window layout, dialogs, and presentation-only formatting. It receives display-ready state from the controller and reports user intent through callbacks. It must not directly mutate models or perform filesystem operations.

### Controller

The controller handles view events, validates the requested workflow through model services, starts background work when needed, and schedules view updates back on Tkinter's main thread. It must not reach into widget internals or duplicate filesystem rules.

### Threading, path changes, and shutdown

- The Tkinter main thread is the only thread allowed to create, read, or update widgets.
- Run directory scans and move batches on a single background worker. Only one scan or move batch may be active at a time.
- Communicate worker progress and results through a thread-safe queue. The controller periodically drains the queue using Tkinter's `after()` scheduling.
- Disable path controls and conflicting actions while an operation is running.
- Assign every scan a monotonically increasing generation identifier. Discard results whose generation does not match the current configured paths.
- Changing either root validates both roots, increments the generation, clears the previous in-memory package list, and starts a fresh scan only after valid paths are confirmed.
- Closing during a read-only scan may request cancellation and then close after the worker exits. Cancellation is cooperative rather than forced.
- Never deliberately interrupt an active package move. When the user requests close during a move, keep the window alive, explain that the move must finish, and close only after receiving its result.
- Worker threads must not prevent a clean process exit after all filesystem work is complete. Log unexpected worker exceptions and convert them into structured failure results.

### Proposed modules

Keep the project compact while giving every primary class its own module:

```text
src/fs24_mod_manager/
├── __init__.py
├── app.py                    # composition root and startup only
├── config.py                 # Config
├── models/
│   ├── app_state.py          # AppState
│   ├── error_code.py         # ErrorCode
│   ├── operation_result.py   # OperationResult
│   ├── package_info.py       # PackageInfo
│   ├── path_validation_result.py # PathValidationResult
│   └── user_settings.py      # UserSettings
├── services/
│   ├── community_locator.py  # CommunityLocator
│   ├── package_scanner.py    # PackageScanner
│   ├── package_mover.py      # PackageMover
│   ├── instance_lock.py      # InstanceLock
│   ├── settings_store.py     # SettingsStore
│   └── state_serializer.py   # StateSerializer
├── views/
│   └── main_view.py          # MainView
└── controllers/
    └── main_controller.py    # MainController
tests/
├── models/
├── services/
└── controllers/
```

Names and exact structure may change during implementation, but the MVC dependency boundaries, one-primary-class-per-module rule, typing, and documentation rules are mandatory. Avoid service containers, plugin systems, and unused framework-like abstractions.

## 10. Error cases to design for

- Community path does not exist or is not writable.
- Disabled path does not exist, is read-only, is inside Community, or is on another drive.
- Two installed package locations are detected.
- A package has missing or malformed JSON metadata.
- The same directory name exists in enabled and disabled storage.
- Package names differ only by letter case or manifests report duplicate identities.
- A stale scan finishes after the user changes either configured path.
- A file is locked or access is denied.
- A move is interrupted or only part of a multi-selection succeeds.
- The user changes paths during a scan.
- The application itself is located directly inside Community.
- A package directory is a junction or symbolic link.

Errors should be actionable and should never cause silent overwrite, merge, or deletion.

## 11. Testing strategy

Automated tests must use temporary directories and fake package manifests; they must never operate on the user's real simulator directories.

At minimum, test:

- parsing `InstalledPackagesPath` variants;
- path validation and nested-root rejection;
- valid, invalid, and malformed package discovery;
- enable and disable moves;
- name-collision refusal;
- application-directory exclusion;
- symlink/junction handling where the platform permits it;
- settings recovery from missing or invalid JSON;
- partial batch-operation reporting;
- JSON serialization and restoration of `AppState` snapshots;
- case-insensitive directory and manifest-identity conflict detection;
- structured success and failure `OperationResult` values;
- cross-volume move rejection;
- stale scan-generation result rejection;
- close requests during scans and active moves;
- controller behavior with model and view test doubles, without starting a real Tkinter window;
- enforcement of model independence from Tkinter imports.

Add a small manual smoke-test checklist for path picking, scanning, searching, multi-selection, error dialogs, and restart persistence.

The automated quality checks must run `mypy --strict`, Ruff formatting and lint checks, and a documentation check capable of catching missing class or method docstrings. If no existing tool reliably enforces the required `@param` convention, add a small focused test for it.

## 12. Version-one acceptance criteria

The first usable version is complete when:

- it starts without administrator rights on a supported Windows system;
- it discovers a likely FS24 Community directory or clearly asks the user to select one;
- the user can change and persist both configured directories;
- it lists valid enabled and disabled packages without scanning recursively;
- it can enable or disable one or several packages using directory moves;
- it refuses collisions and unsafe/nested paths without modifying data;
- it rejects cross-volume moves in version one;
- it prevents concurrent operations and safely handles path changes and close requests;
- every requested package in a batch receives a structured operation result;
- it never manages or moves its own application directory;
- failures are visible, logged, and do not crash the UI;
- filesystem logic has automated coverage using temporary test data;
- the implementation follows the defined MVC import boundaries;
- each primary class has its own module and all classes and methods follow the required docstring convention;
- strict static type checking passes on Python 3.13 or newer;
- current application state can be represented as JSON without becoming an authoritative package database;
- no feature depends on links, junctions, downloads, or a database.

## 13. Decisions to revisit before implementation

1. Final application name and Python package name.
2. Exact FS24 Store/Xbox and Steam discovery locations to support and verify.
3. Whether invalid folders should be visible in the main table or only summarized.
4. Whether the app should check for a running simulator process or rely on a standing warning.
5. Whether package metadata fields are consistent enough across real FS24 mods to add creator/type columns.
6. Distribution format: source-only, a standalone executable, or both.
7. Public distribution license.

## 14. Explicit non-goals for the first version

- Mod downloads, updates, ratings, or online catalogs.
- Profiles/presets and automatic conflict resolution.
- Editing `layout.json`, `manifest.json`, or simulator configuration.
- Symbolic links, directory junctions, or virtual filesystems.
- Automatic backups or archive compression.
- Watching the directories continuously.
- Launching or controlling Flight Simulator.
- Supporting non-Windows operating systems.

## 15. Settings schema and recovery

The settings JSON must contain a numeric `settings_version`. `Config` defines the current version and every default value. `SettingsStore` owns serialization, validation, migration, and recovery.

- Serialize paths as strings and convert them into resolved `Path` values only after validation.
- Accept missing optional fields by applying defaults.
- Treat invalid types, an unsupported version, or malformed JSON as an invalid settings document.
- Before replacing an invalid settings file, preserve it beside the new file with a timestamped `.invalid.json` suffix when possible.
- Write a new file to the same directory, flush and close it, and atomically replace the previous settings file.
- Never treat values loaded from settings as trusted filesystem paths; apply the same validation used for paths selected through the UI.

Initial shape:

```json
{
  "settings_version": 1,
  "community_path": "D:\\...\\Packages\\Community",
  "disabled_path": "D:\\...\\Packages\\Community_disabled",
  "window_geometry": "1000x650"
}
```

## 16. Error and operation contracts

Define an `ErrorCode` enum with stable, machine-readable members. The initial set should include:

- `SOURCE_MISSING`
- `DESTINATION_EXISTS`
- `PATH_NOT_WRITABLE`
- `CROSS_VOLUME`
- `PACKAGE_INVALID`
- `PACKAGE_CONFLICT`
- `ACCESS_DENIED`
- `FILE_LOCKED`
- `OPERATION_CANCELLED`
- `UNEXPECTED_ERROR`

`OperationResult` carries an operation identifier, package identity, requested action, success flag, source, destination, optional `ErrorCode`, user-facing message, and optional technical details. UI code chooses presentation; services provide facts and stable codes. Technical details and tracebacks belong in logs and must not be shown as the primary user message.

Every move must be revalidated immediately before execution. After a reported successful move, verify that the source no longer exists, the destination exists, and the destination still contains its root `manifest.json` and `layout.json`. Update model state only after verification. Rescan both roots after the full batch.

If post-move verification fails, report an uncertain state, do not attempt an automatic destructive rollback, and tell the user which source and destination paths to inspect. Failure and recovery messages must state what was attempted, what completed, whether rescanning is safe, and where logs are stored.

## 17. Logging and privacy

Write size-limited rotating logs under `%LOCALAPPDATA%\FS24ModManager`. `Config` owns the size and retention defaults.

Logs should include timestamps, severity, operation and scan identifiers, relevant source/destination paths, stable result codes, and exception tracebacks. Never log complete manifest contents or unrelated directory contents. The application must not collect analytics, contact telemetry services, or transmit paths and package information.

Provide an **Open log folder** action. If the folder cannot be opened, show its selectable full path instead.

## 18. Composition and dependency ownership

The startup composition order is:

```text
App entry point
  -> Config
  -> SettingsStore
  -> models and filesystem services
  -> MainView
  -> MainController
  -> Tkinter main loop
```

Only the composition root constructs the dependency graph. Classes receive required collaborators through constructors. Do not use global service locators, hidden singleton dependencies, or imports that construct application services as side effects.

## 19. Single-instance and external-change behavior

Version one permits only one running manager instance per user. Use an application lock file under `%LOCALAPPDATA%\FS24ModManager` containing the owning process identifier and sufficient metadata to diagnose a stale lock. Recover a stale lock only after verifying that its owning process no longer exists. A second active instance must exit without modifying packages and should focus the first window if a simple reliable Windows implementation is available; otherwise it displays an explanatory message.

The filesystem may change through Explorer or another application while the manager is open:

- Revalidate paths, source existence, package validity, conflicts, and destination absence immediately before every move.
- A manual refresh replaces the complete in-memory package snapshot.
- Preserve selected rows across refresh only when their stable package identities still exist.
- Never authorize a move solely from previously displayed state.
- Do not add continuous filesystem watching in version one.

## 20. Search, ordering, and accessibility

- Sort package names case-insensitively with a deterministic directory-name tie breaker.
- Search display name, directory name, creator/manufacturer, and version case-insensitively.
- Show enabled, disabled, conflicted, and invalid states with text or icons; color must not be the only indicator.
- Make all actions keyboard accessible with a logical tab order and documented shortcuts.
- Use `Ctrl+A` to select all visible rows, `Escape` to clear selection, and `F5` to refresh.
- Destructive or state-changing confirmation dialogs default to the safe cancel action.
- Make long paths selectable and copyable, and allow table columns to be resized.
- Persist useful window geometry, but clamp restored coordinates and dimensions to the currently visible desktop after monitor changes.

## 21. Repository deliverables and continuous integration

The repository must include:

- `pyproject.toml` with project metadata and Ruff, mypy, and pytest configuration;
- `requirements.txt` for runtime dependencies;
- `requirements-dev.txt` for development tools;
- `requirements-build.txt` for isolated executable-build dependencies;
- `README.md` with setup, development commands, safety behavior, and supported Python versions;
- `AGENTS.md` containing implementation constraints for coding agents;
- `ARCHITECTURE.md` describing implemented MVC boundaries, threading, state, and safety flow;
- `.gitignore`;
- `build.bat` for producing the standalone Windows executable;
- `installer.bat` and `packaging/installer.iss` for producing a registered Windows installer;
- `deploy.bat` for producing a clean source-distribution ZIP under `dist`;
- a `src` package layout and mirrored `tests` structure;
- a GitHub Actions workflow running on Windows against the minimum supported Python 3.13 and the newest stable Python version adopted by the project.

Continuous integration must run Ruff formatting checks, Ruff linting, `mypy --strict`, and pytest without Flight Simulator installed and without accessing any real Community directory. A license must be selected by the repository owner before public distribution; do not infer or add one automatically.

`deploy.bat` must be runnable from any working directory, validate its required inputs, and create `dist\flightsimulator_mod_manager.zip`. Include `src`, `packaging`, `README.md`, `SPECIFICATION.md`, `ARCHITECTURE.md`, `pyproject.toml`, `requirements.txt`, `requirements-build.txt`, `build.bat`, `installer.bat`, and `LICENSE` when present. Exclude tests, Git and GitHub metadata, agent instructions, development test requirements, caches, logs, local settings, and virtual environments. Repeated execution may replace only that exact generated archive.

`build.bat` must also be runnable from any working directory. It selects the newest installed Python 3 interpreter, validates that it is Python 3.13 or newer, validates the application entry point, creates an isolated temporary virtual environment, installs runtime and build requirements, and invokes PyInstaller in one-file windowed mode. The only persistent build artifact is `dist\FlightSimulatorModManager.exe`; temporary environments, generated `.spec` files, and PyInstaller work output must be removed after success or failure. It may replace only that exact executable and must not clear unrelated contents from `dist`.

`installer.bat` accepts an optional semantic version, rebuilds the application executable, prefers the Inno Setup 7 compiler with an Inno Setup 6 compatibility fallback, and creates `dist\FlightSimulatorModManager-<version>-Setup.exe`. The installer must default to per-user installation without administrator rights, register under Windows Installed apps, create a Start Menu shortcut discoverable through Windows Search, offer an unchecked optional desktop shortcut, and provide an uninstaller. The Inno Setup definition belongs in `packaging/installer.iss`; compiled installers remain ignored build artifacts.

## 22. Version policy

The project version is `0.1.0` throughout the current development cycle and remains `0.1.0` until that version is formally released. The Python package metadata, visible application version, executable/installer build inputs, documentation, and release artifacts must agree. Version advancement happens only after the `0.1.0` release is complete and the repository owner explicitly selects the next version.
