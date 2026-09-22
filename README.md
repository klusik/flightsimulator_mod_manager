# Flight Simulator Mod Manager

A Windows desktop application for enabling and disabling Microsoft Flight Simulator 2024 Community packages through safe directory moves.

The project has a functional first implementation and remains under active development. See [SPECIFICATION.md](SPECIFICATION.md) for the product and safety contract and [ARCHITECTURE.md](ARCHITECTURE.md) for the implemented component design.

## Core approach

- Python 3.13 or newer with Tkinter and `ttk`.
- Enabled packages are direct children of the configured `Community` directory.
- Disabled packages are moved to a configurable directory outside `Community`.
- The suggested disabled path for `C:\something\Community` is `C:\something\Community_disabled`.
- Packages are moved as complete directories; their contents are not edited.
- Cross-volume moves, destination conflicts, links, merges, overwrites, and deletions are rejected in version one.
- Close Flight Simulator before changing package state.

## Using the interface

- Choose or confirm the active Community and disabled-mods directories.
- Use the search field to filter by title, directory, creator, manufacturer, or version.
- Package states use symbols as well as words: `●` enabled, `○` disabled, `⚠` conflicted, and `✕` invalid.
- **Select all** selects every visible filtered row; **Clear** removes the selection.
- Use `Ctrl+A` to select visible rows, `Escape` to clear selection, and `F5` to refresh.
- Enable and disable buttons activate only when the current selection contains applicable packages.
- Both table scrollbars support large package collections and long metadata.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the implemented component and threading design.

## Development setup

Create and activate a virtual environment with the newest installed Python 3 interpreter, then install the development requirements. The selected interpreter must be Python 3.13 or newer:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Run all quality checks:

```powershell
python -m ruff format --check .
python -m ruff check .
python -m mypy src
python -m pytest
```

Tests must use temporary directories and must never operate on an actual simulator installation.

## Build the Windows executable

After the application entry point exists, run:

```powershell
.\build.bat
```

The script selects the newest installed Python 3 interpreter, requires it to be Python 3.13 or newer, and needs internet access for installing the isolated build dependency. It creates a temporary virtual environment outside the repository, builds a single windowed executable with PyInstaller, writes `dist\FlightSimulatorModManager.exe`, and removes its temporary environment, work directory, and generated specification file. It replaces only the executable with that exact output name and does not remove other files from `dist`.

## Create a deployment archive

Run the deployment script from any working directory:

```powershell
.\deploy.bat
```

It creates `dist\flightsimulator_mod_manager.zip`, replacing only an existing archive with that exact name. The ZIP contains the application source, runtime requirements, project metadata, specification, README, and `LICENSE` when one exists. Development tools, tests, repository metadata, caches, and local settings are excluded.

## Project status

The first implementation draft includes the typed model and service layers, safe package scanning and moves, settings persistence, Community discovery, a Tkinter MVC interface, and executable packaging. Remaining version-one work is tracked against `SPECIFICATION.md`.

## License

No license has been selected yet. The repository owner must choose one before public distribution or reuse is authorized.
