# Flight Simulator Mod Manager

A planned Windows desktop application for enabling and disabling Microsoft Flight Simulator 2024 Community packages through safe directory moves.

The project is currently in its specification and scaffolding phase. Application behavior has not yet been implemented. See [SPECIFICATION.md](SPECIFICATION.md) for the complete product, safety, architecture, and acceptance requirements.

## Core approach

- Python 3.13 or newer with Tkinter and `ttk`.
- Enabled packages are direct children of the configured `Community` directory.
- Disabled packages are moved to a configurable directory outside `Community`.
- The suggested disabled path for `C:\something\Community` is `C:\something\Community_disabled`.
- Packages are moved as complete directories; their contents are not edited.
- Cross-volume moves, destination conflicts, links, merges, overwrites, and deletions are rejected in version one.
- Close Flight Simulator before changing package state.

## Development setup

Create and activate a Python 3.13 virtual environment, then install the development requirements:

```powershell
py -3.13 -m venv .venv
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

## Create a deployment archive

Run the deployment script from any working directory:

```powershell
.\deploy.bat
```

It creates `dist\flightsimulator_mod_manager.zip`, replacing only an existing archive with that exact name. The ZIP contains the application source, runtime requirements, project metadata, specification, README, Python version declaration, and `LICENSE` when one exists. Development tools, tests, repository metadata, caches, and local settings are excluded.

## Project status

The repository contains planning and development configuration only. Implementation should follow `SPECIFICATION.md` and `AGENTS.md`.

## License

No license has been selected yet. The repository owner must choose one before public distribution or reuse is authorized.
