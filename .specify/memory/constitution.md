<!--
Sync Impact Report
- Version change: [TEMPLATE] → 1.0.0 (initial ratification)
- Modified principles: n/a (first concrete fill of the template; all placeholders replaced)
- Added sections: Core Principles (I-V), Technology Constraints, Development Workflow, Governance
- Removed sections: none
- Templates requiring follow-up: none — plan/spec/tasks templates consume this file at runtime
  and were not modified per the scope guard of this command.
- Deferred placeholders: none; RATIFICATION_DATE set to the date this constitution was first
  adopted since no prior ratified version existed (the file previously held only unfilled
  template placeholders).
-->

# monetils Constitution

## Core Principles

### I. Zero Runtime Dependencies (Library-First)
`monetils` MUST declare no runtime dependencies (`dependencies = []` in `pyproject.toml`).
Any proposed runtime dependency requires an explicit, documented justification in the PR
description and MUST be approved before merge; prefer implementing small utilities in-house
over adding a dependency. Test and dev tooling (pytest, ruff, tox, pre-commit, etc.) are exempt
and belong in `[project.optional-dependencies]` / `[dependency-groups]` only.
Rationale: this is a small, embeddable utility library; a heavy dependency graph undermines its
core value proposition and creates version-conflict risk for every consumer.

### II. Test-First & High Coverage (NON-NEGOTIABLE)
New behavior MUST be covered by tests in `tests/` before a PR is considered done. Line coverage
of `src/monetils` MUST stay at or above the `fail_under = 90` threshold configured in
`[tool.coverage.report]`; a change that drops coverage below this bar MUST NOT be merged without
either added tests or an explicit, reviewed exception. CI MUST pass `uv run pytest` on Python
3.11, 3.12, and 3.13 (the matrix in `.github/workflows/tests.yml`) before merge.
Rationale: monetary-value arithmetic is exactly the kind of code where silent off-by-one or
rounding bugs are costly; strong test coverage across supported interpreters is the primary
defense.

### III. Typed Public API
All public modules, functions, classes, and methods exported from `src/monetils` MUST carry
complete type hints, and the package MUST continue to ship `py.typed` so consumers get static
type checking. Untyped or `Any`-typed public signatures require explicit justification in the
PR description.
Rationale: consumers use this library to represent money safely; type signatures are part of the
correctness contract and let downstream type checkers catch misuse before runtime.

### IV. Lint & Format Enforcement
Code MUST pass `uv run ruff check .` and `uv run ruff format --check .` (or the pre-commit
`ruff` / `ruff-format` hooks) before merge, using the rule set already configured in
`[tool.ruff.lint]` (pycodestyle, pyflakes, isort, pyupgrade, bugbear, comprehensions, simplify,
bandit security checks, naming, pylint, return/argument checks). Rule-set changes (adding,
removing, or ignoring a rule category) MUST be made in `pyproject.toml` and called out in the PR,
not silenced ad hoc with inline `# noqa` unless a one-off exception is genuinely warranted.
Rationale: a single, enforced lint/format configuration keeps a small library's codebase
consistent and catches an entire class of bugs (including basic security issues via the bandit
ruleset) automatically.

### V. Semantic Versioning & Backward Compatibility
`monetils` is published to PyPI and TestPyPI and MUST follow semantic versioning
(`MAJOR.MINOR.PATCH`) as declared in `pyproject.toml`. Breaking changes to any public API
(function signatures, class interfaces, module paths) require a MAJOR version bump and MUST be
called out explicitly in the PR description and release notes; new backward-compatible
functionality bumps MINOR; fixes and internal changes bump PATCH.
Rationale: external consumers pin against published versions; predictable versioning is the
contract that lets them upgrade safely.

## Technology Constraints

- Python: support the versions declared in `pyproject.toml` classifiers and the CI matrix
  (currently 3.11, 3.12, 3.13); `requires-python` MUST NOT be loosened without updating both the
  classifiers and the CI matrix in the same change.
- Dependency management: `uv` is the required tool for environment sync (`uv sync`), running
  tests (`uv run pytest`), and running lint/format (`uv run ruff ...`). Do not introduce a
  parallel tool (pip-tools, poetry, etc.) without a constitution amendment.
- Build backend: `hatchling`, with the wheel packaging `src/monetils` as configured in
  `[tool.hatch.build.targets.wheel]`. Changes to the build backend or package layout require
  explicit review since they affect the published distribution.

## Development Workflow

- Local changes MUST be validated with `uv run pytest` and `uv run ruff check --fix .` /
  `uv run ruff format .` before opening a PR; pre-commit hooks (`.pre-commit-config.yaml`)
  provide the same checks locally (ruff, ruff-format, trailing-whitespace, end-of-file-fixer,
  check-yaml, check-added-large-files) and MUST NOT be bypassed with `--no-verify` except for a
  documented, user-approved reason.
- CI (`.github/workflows/tests.yml`) running the full pytest suite across the supported Python
  matrix is a required merge gate; `publish-testpypi.yml` / `publish-pypi.yml` govern releases
  and MUST NOT be modified to skip tests as a path to publishing.
- PRs that change public behavior MUST update `README.md` and any relevant docstrings in the
  same change, not as a follow-up.

## Governance

This constitution supersedes ad hoc practice for `monetils`. Amendments are made via this same
`/speckit-constitution` workflow: propose the change, update this file, increment the version
per the semantic rule below, and record the change in the Sync Impact Report at the top of this
file.

Versioning policy for this document (independent of the package's own semantic version):
- MAJOR: backward-incompatible governance changes, or removal/redefinition of a principle.
- MINOR: a new principle or materially expanded section is added.
- PATCH: wording clarifications, typo fixes, non-semantic refinements.

Compliance review: every PR MUST be checked against the five Core Principles above (dependency
additions, test coverage, typing, lint/format, and versioning impact) before merge; a reviewer
who overrides one of these MUST record the justification in the PR description. Use
`CLAUDE.md` for day-to-day agent operating instructions (setup and command shortcuts); this
constitution is the authority when the two conflict.

**Version**: 1.0.0 | **Ratified**: 2026-09-04 | **Last Amended**: 2026-09-04
