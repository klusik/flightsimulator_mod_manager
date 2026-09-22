# FS24 Community Mod Manager — First-Draft Build Brief

> Temporary planning document. Refine this specification before implementation.

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
├── Official/
└── _DisabledMods/
    └── another-aircraft-mod/
```

The default disabled path should therefore be:

```text
<Community parent>\_DisabledMods
```

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
- Runtime: a maintained Python 3 release.
- GUI: standard-library Tkinter and `ttk`.
- File operations: `pathlib` and `shutil`/`os` as appropriate.
- Persistence: a small human-readable JSON settings file in the user's local application-data directory, not in `Community`.
- Logging: a rotating or size-limited text log in the same application-data directory.
- Packaging can be considered later; development starts as a normal Python application.

Prefer the standard library unless a dependency provides clear value. The initial version should not require administrator rights.

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

## 5. Package detection

Treat only **direct child directories** of each configured root as package candidates. Do not recursively combine nested packages.

A directory is a valid package when it contains both of these files at its root:

- `manifest.json`
- `layout.json`

File-name comparison should accommodate Windows case-insensitivity. Malformed JSON should not crash scanning; show the directory as invalid or unreadable with a diagnostic. Direct child folders without both files are not manageable mods and may optionally appear in a separate warning/status count.

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
- columns for name, version, directory, and status;
- **Enable** and **Disable** actions, disabled when they do not apply;
- a status line with package counts and the result of the latest operation;
- a compact error dialog for failed operations, with details recorded in the log.

Allow selecting multiple packages for a batch enable/disable operation. The interface should remain responsive; scanning and moves may run through a worker thread, but all Tkinter widget updates must occur on the main UI thread.

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

Create the configured disabled-mods directory only after explicit user confirmation or the first disable action. If the source and destination are on different volumes, explain that the operation becomes copy-then-delete and can take longer. On failure, report exactly which package failed and leave already completed independent moves recorded in the result; do not claim an all-or-nothing batch transaction.

Do not delete package directories. Do not edit manifests. Do not follow directory junctions or symbolic links during scans. A link itself should be skipped and reported to avoid moving data outside the selected roots unexpectedly.

## 8. Configuration and application data

Store only application preferences, for example:

```json
{
  "community_path": "D:\\...\\Packages\\Community",
  "disabled_path": "D:\\...\\Packages\\_DisabledMods",
  "window_geometry": "1000x650"
}
```

Use an application-data location such as `%LOCALAPPDATA%\FS24ModManager`. Write settings safely through a temporary file followed by replacement so an interrupted save is unlikely to corrupt them.

Do not store absolute package inventories as authoritative state. The filesystem is the source of truth and is rescanned at startup and on request.

## 9. Suggested code boundaries

Keep the project compact, but separate testable filesystem behavior from Tkinter:

```text
src/fs24_mod_manager/
├── __init__.py
├── app.py             # startup and composition
├── discovery.py       # installation and Community-path discovery
├── packages.py        # scan, metadata, validation, and moves
├── settings.py        # JSON preferences and app-data paths
└── ui.py              # Tkinter widgets and event handling
tests/
├── test_discovery.py
├── test_packages.py
└── test_settings.py
```

Names and exact structure may change during implementation. Avoid framework-like abstractions, repositories, service containers, or plugin systems unless later requirements justify them.

## 10. Error cases to design for

- Community path does not exist or is not writable.
- Disabled path does not exist, is read-only, is inside Community, or is on another drive.
- Two installed package locations are detected.
- A package has missing or malformed JSON metadata.
- The same directory name exists in enabled and disabled storage.
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
- partial batch-operation reporting.

Add a small manual smoke-test checklist for path picking, scanning, searching, multi-selection, error dialogs, and restart persistence.

## 12. Version-one acceptance criteria

The first usable version is complete when:

- it starts without administrator rights on a supported Windows system;
- it discovers a likely FS24 Community directory or clearly asks the user to select one;
- the user can change and persist both configured directories;
- it lists valid enabled and disabled packages without scanning recursively;
- it can enable or disable one or several packages using directory moves;
- it refuses collisions and unsafe/nested paths without modifying data;
- it never manages or moves its own application directory;
- failures are visible, logged, and do not crash the UI;
- filesystem logic has automated coverage using temporary test data;
- no feature depends on links, junctions, downloads, or a database.

## 13. Decisions to revisit before implementation

1. Final application name and Python package name.
2. Exact FS24 Store/Xbox and Steam discovery locations to support and verify.
3. Whether invalid folders should be visible in the main table or only summarized.
4. Whether cross-volume moves are allowed with a warning or rejected in version one.
5. Whether the app should check for a running simulator process or rely on a standing warning.
6. Whether package metadata fields are consistent enough across real FS24 mods to add creator/type columns.
7. Distribution format: source-only, a standalone executable, or both.

## 14. Explicit non-goals for the first version

- Mod downloads, updates, ratings, or online catalogs.
- Profiles/presets and automatic conflict resolution.
- Editing `layout.json`, `manifest.json`, or simulator configuration.
- Symbolic links, directory junctions, or virtual filesystems.
- Automatic backups or archive compression.
- Watching the directories continuously.
- Launching or controlling Flight Simulator.
- Supporting non-Windows operating systems.

