# Patch Notes Generation Template

This document defines the required format for maintainers and agents adding entries to `PATCH_NOTES.md`.

Do not overwrite existing patch notes. Add the newest version above older versions and preserve the established Markdown structure.

## Version numbering rules

- Use semantic versioning in `X.Y.Z` form.
- Use numeric identifiers without leading zeroes.
- Keep the runtime version, package metadata, documentation, installer, archive names, intended Git tag, and patch-note heading consistent.
- Do not advance the version until the repository owner explicitly selects the next version.

## Required structure

```markdown
## Version X.Y.Z

Short release summary explaining the release purpose and most important changes.

### Highlights

#### Added or changed area

- Describe user-visible changes as completed actions.
- Group related behavior together.

### Technical Details

#### Application architecture

- Describe model, service, controller, view, threading, or configuration changes.

#### Persistence and compatibility

- Describe settings-format, filesystem, operating-system, and Python compatibility changes.

#### Quality and release tooling

- Describe tests, automation, builds, installers, and packaging changes.

### Tests

#### Automated coverage

- Describe the behavior covered and the release checks actually completed.
- State material skipped or unavailable coverage explicitly.

### User Impact

#### For players

- Describe workflow improvements, compatibility notes, and any required user action.

#### Distribution notes

- Describe signing, licensing, installation, migration, or packaging considerations.
```

## Formatting rules

- Use a level-two heading for each version, level-three main sections, and level-four feature groups.
- Use bullet lists for individual changes.
- Use past tense such as "Added", "Updated", "Fixed", and "Improved".
- Wrap filenames, paths, commands, identifiers, settings keys, and keyboard shortcuts in backticks.
- Reference complete repository-relative paths where useful.
- Avoid vague entries such as "changed some files".
- Do not include a claim that a test, build, installation, or manual check passed unless it was completed for that release candidate.

## Content expectations

A complete entry should consider:

- user-facing changes;
- filesystem safety and recovery behavior;
- MVC, threading, model, service, and persistence changes;
- supported Windows and Python versions;
- configuration or settings-format changes;
- tests added or changed and material coverage gaps;
- executable, archive, installer, and GitHub Release changes;
- upgrade or compatibility notes;
- known limitations, signing status, and licensing status.

Keep each entry detailed enough that a user can understand the release without reading Git history.

