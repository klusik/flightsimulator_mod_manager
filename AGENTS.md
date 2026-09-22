# Agent Instructions

These instructions apply to the entire repository.

## Source of truth

Read `SPECIFICATION.md` completely before designing or changing application behavior. Treat it as the product and architecture contract. If implementation and specification disagree, stop and resolve the discrepancy explicitly rather than silently choosing one.

## Required engineering rules

- Support Python 3.13 and newer.
- Never use `from __future__ import annotations`.
- Follow the strict MVC boundaries defined in `SPECIFICATION.md`.
- Keep business behavior in cohesive classes and define one primary public class per module.
- Use typed dataclasses for application state and value objects where appropriate.
- Type every class attribute, method parameter, and return value. All source must pass `mypy --strict`.
- Give every class and every method a meaningful docstring.
- Use `@param <name>:`, `@return:`, and `@raises <Exception>:` in method docstrings as applicable.
- Keep configuration defaults in the `Config` class. Do not introduce mutable global state.
- Inject collaborators through constructors. Do not introduce service locators or hidden singleton dependencies.
- Keep Tkinter access on the main thread. Models and services must not import Tkinter.
- Preserve the filesystem as the authoritative package state. JSON is configuration or a serializable snapshot, never a package database.
- Never merge, overwrite, delete, or recursively relocate a package to resolve a conflict.
- Reject cross-volume package moves in version one.

## Scope control

Prefer small, direct classes over speculative abstractions. Do not add profiles, downloads, dependency resolution, symbolic links, junctions, live filesystem watching, telemetry, a database, or other explicit non-goals unless the specification is first changed with owner approval.

## Verification

Run these checks before handing off code changes:

```powershell
python -m ruff format --check .
python -m ruff check .
python -m mypy src
python -m pytest
```

Tests must use temporary directories and synthetic manifests. They must never read from or write to a real Flight Simulator Community directory.

## Repository hygiene

- Keep generated files, virtual environments, caches, logs, and local settings out of Git.
- Update `SPECIFICATION.md` and `README.md` when an approved behavior or workflow changes.
- Do not add a license until the repository owner selects one.
- Do not commit or push unless the user explicitly asks.
