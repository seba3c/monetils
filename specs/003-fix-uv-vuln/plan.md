# Implementation Plan: Uv Dependency Vulnerability Remediation

**Branch**: `003-fix-uv-vuln` | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-fix-uv-vuln/spec.md`

## Summary

Regenerate `uv.lock` so the transitively-pinned `uv` package (pulled in by the `tox-uv` dev dependency) resolves to `0.11.15` or later, closing GitHub Dependabot alert #1 (GHSA-4gg8-gxpx-9rph, an arbitrary-file-write vulnerability in `uv` versions before 0.11.15). No source code, public API, or runtime dependency changes — this is a lockfile-only maintenance fix, verified by re-running the existing test suite.

## Technical Context

**Language/Version**: Python 3.11–3.13 (existing project matrix; unchanged)

**Primary Dependencies**: N/A — no new dependency is introduced. `uv` is an existing *transitive* dev dependency (via `tox-uv`, itself in `[dependency-groups].dev` and the `test` extra); only its resolved version in `uv.lock` changes.

**Storage**: N/A

**Testing**: `uv run pytest` (existing suite, 79 tests) — used to confirm no regression from the dependency bump

**Target Platform**: N/A (library; fix affects local/CI dev tooling only, not the published wheel)

**Project Type**: Library (existing `monetils` structure; no structural change)

**Performance Goals**: N/A

**Constraints**: MUST NOT add or change any entry in `pyproject.toml`'s runtime `dependencies = []` (Constitution Principle I); MUST NOT require an explicit `uv` version pin anywhere, since no such pin currently exists and none is needed — only the lockfile's resolved version changes

**Scale/Scope**: Single file (`uv.lock`) regenerated via `uv lock --upgrade-package uv`; no other files change as part of the fix itself

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|---|---|
| I. Zero Runtime Dependencies | **PASS** — `uv` is dev-tooling only, resolved transitively via `tox-uv` in `[dependency-groups].dev` / the `test` extra; `pyproject.toml`'s runtime `dependencies = []` is untouched. |
| II. Test-First & High Coverage | **PASS** — no new behavior or code path is introduced, so no new tests are required; the existing suite (`uv run pytest`, 79 tests) MUST still pass unmodified after the lockfile regeneration, which is this feature's acceptance check. |
| III. Typed Public API | **N/A** — no public API surface changes. |
| IV. Lint & Format | **PASS** — no Python source changes; `uv.lock` is a generated, non-linted file. |
| V. Semantic Versioning | **Applies at implementation time** — this is a fix/internal change, so it bumps `PATCH` per the constitution's rule ("fixes and internal changes bump PATCH"). The project's `speckit-version-bump` extension will prompt for this automatically after `/speckit-implement` runs. |

No violations; Complexity Tracking is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/003-fix-uv-vuln/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command) — N/A, no entities
├── quickstart.md        # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

No `contracts/` directory: this fix changes no public interface (no API, CLI, or contract surface) — it is purely internal dependency-lockfile maintenance.

### Source Code (repository root)

```text
uv.lock                  # The only file this feature modifies
tests/test_placeholder.py  # Existing test re-run (unmodified) to verify no regression
```

**Structure Decision**: No new modules, packages, or directories. This feature touches exactly one existing file, `uv.lock`, at the repository root — the existing single-project `src/monetils/` + `tests/` layout is unaffected.

## Complexity Tracking

*No Constitution Check violations — this section is not needed.*
