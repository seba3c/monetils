# Implementation Plan: Pydantic v2 Model Field Support

**Branch**: `002-pydantic-model-support` | **Date**: 2026-09-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-pydantic-model-support/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Make `BTC` and `USD` directly usable as Pydantic v2 model field annotations (`amount: USD`, `amount: BTC | None`) with no wrapper type required. Implement Pydantic's custom-type protocol (`__get_pydantic_core_schema__` / `__get_pydantic_json_schema__`) once on the private shared `_Currency` base so both currencies — and any future currency built on it — gain support automatically. Validation accepts a same-class instance unchanged (exact precision), or a plain number/numeric string interpreted the same way the existing `BTC(value)`/`USD(value)` constructor already does; anything else (wrong-currency instance, unparseable value) is translated into a standard `pydantic.ValidationError`. Python-mode dumps (`model_dump()`) return the instance itself; JSON-mode dumps (`model_dump_json()`, `model_dump(mode="json")`) and JSON Schema generation reuse the existing fixed-decimal `str()` convention. `pydantic>=2.0,<3` is added only as a test/development dependency — `monetils` remains a zero-runtime-dependency package (Constitution Principle I fully preserved, no amendment needed). The two Pydantic hook methods on `_Currency` import `pydantic_core` lazily, inside their own bodies, so plain `import monetils` and all direct (non-Pydantic) usage keep working with no third-party runtime dependency installed at all (FR-010).

## Technical Context

**Language/Version**: Python 3.11+ (unchanged; existing `requires-python` floor and CI matrix — 3.11, 3.12, 3.13)

**Primary Dependencies**: `pydantic>=2.0,<3` — **test/development-only dependency** (FR-009), added to `[project.optional-dependencies].test` and `[dependency-groups].dev`, never to `[project.dependencies]`. Existing dev/test tooling (`pytest`, `pytest-cov`, `ruff`, `tox`) is otherwise unchanged. The `_Currency` Pydantic hooks import `pydantic_core` lazily at call-time (FR-010), so `monetils` has zero third-party runtime dependencies, same as before this feature.

**Storage**: N/A — no persistence; this feature only affects in-memory validation/serialization of existing value objects.

**Testing**: `pytest` + `pytest-cov` via `uv run pytest --cov=src/monetils` (coverage gate `fail_under = 90` in `pyproject.toml` is unchanged and must still hold with the new code included); `tox` runs the suite across the Python 3.11/3.12/3.13 matrix. New tests construct real `pydantic.BaseModel` subclasses with `BTC`/`USD` fields and exercise construction, `model_dump()`, `model_dump_json()`, and `model_json_schema()` directly — no mocking of Pydantic itself.

**Target Platform**: Unchanged — any OS running a supported CPython version; distributed as a pure-Python wheel via PyPI/TestPyPI (still zero runtime dependencies — `pydantic` is test/dev-only, FR-009/FR-010).

**Project Type**: Single-package library (existing `src/monetils/` layout) — no CLI, service, or UI component; no new public symbols are exported from `monetils/__init__.py` (FR-008).

**Performance Goals**: Not performance-critical, consistent with feature 001. Pydantic-core validation overhead for a `BTC`/`USD` field is not a target for this feature.

**Constraints**: Constitution Principle I (Zero Runtime Dependencies) MUST remain fully satisfied — `pydantic` is never added to `[project.dependencies]`, and no *other* new dependency (runtime or otherwise) may be introduced to deliver this feature. The Pydantic hooks must live on the private `_Currency` base only (not duplicated per currency), so a future currency (FR-016 of feature 001) inherits Pydantic support with zero additional code, and must import `pydantic_core` lazily inside their own bodies, never at module scope (FR-010). Must not change any existing direct (non-Pydantic) `BTC`/`USD` construction, arithmetic, comparison, conversion, or formatting behavior (FR-008).

**Scale/Scope**: Adds Pydantic compatibility to the 2 existing currency classes through one shared implementation point (`_Currency`); no new public exports, no new currency classes in this feature.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Zero Runtime Dependencies | PASS | `pydantic` is added only to `[project.optional-dependencies].test` and `[dependency-groups].dev` — never to `[project.dependencies]`. The `_Currency` Pydantic hooks import `pydantic_core` lazily inside their own bodies (FR-010), so `monetils` keeps zero third-party runtime dependencies. No constitution amendment or exception needed. |
| II. Test-First & High Coverage | PASS (enforced at implementation) | New behavior lands with tests in `tests/test_pydantic.py`; `tasks.md` must keep `src/monetils` coverage ≥90% across Python 3.11–3.13 including the new code. |
| III. Typed Public API | PASS | `__get_pydantic_core_schema__` and `__get_pydantic_json_schema__` are added as fully typed classmethods on `_Currency` (private) using Pydantic's own typed protocol (`GetCoreSchemaHandler`, `GetJsonSchemaHandler`, `CoreSchema`, `JsonSchemaValue`). No new public symbol is added to `monetils/__init__.py`. |
| IV. Lint & Format Enforcement | PASS | No change to `pyproject.toml`'s `[tool.ruff]` config; new code must pass the existing rule set as-is. |
| V. Semantic Versioning | PASS (MINOR bump) | Purely additive capability — no existing public signature changes (FR-008), and no new runtime dependency footprint either. Exact next version number is decided at release time, consistent with feature 001 not yet having shipped a final `0.2.0`. |

No violations — see Complexity Tracking below. All gates pass; no changes needed after Phase 1 design (re-checked below).

### Post-Phase 1 re-check

Unchanged from the pre-Phase-0 check above: the design in `data-model.md` and `contracts/pydantic_integration.md` adds no runtime dependency, no new public exports, and no changes to existing direct-use behavior. All gates remain PASS.

## Project Structure

### Documentation (this feature)

```text
specs/002-pydantic-model-support/
├── plan.md                        # This file (/speckit-plan command output)
├── research.md                    # Phase 0 output (/speckit-plan command)
├── data-model.md                  # Phase 1 output (/speckit-plan command)
├── quickstart.md                  # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── pydantic_integration.md    # Phase 1 output (/speckit-plan command)
├── checklists/
│   └── requirements.md            # Spec quality checklist (/speckit-specify, /speckit-clarify)
└── tasks.md                       # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/monetils/
├── __init__.py     # Unchanged exports: BTC, USD, MonetilsError, CurrencyMismatchError
├── _base.py        # _Currency gains: __get_pydantic_core_schema__, __get_pydantic_json_schema__,
│                    # and a private _pydantic_validate classmethod helper (research.md)
├── _btc.py         # Unchanged
├── _usd.py         # Unchanged
├── _errors.py      # Unchanged
└── py.typed        # (existing)

tests/
├── __init__.py           # (existing)
├── test_btc.py           # (existing, unchanged)
├── test_usd.py           # (existing, unchanged)
├── test_errors.py        # (existing, unchanged)
└── test_pydantic.py      # New: model field validation, serialization (python + json mode),
                           # JSON schema generation, and ValidationError cases, for both BTC and USD

pyproject.toml
├── [project.optional-dependencies].test   # Add "pydantic>=2.0,<3" (FR-009)
└── [dependency-groups].dev                # Add "pydantic>=2.0,<3" (so `uv sync` installs it for local dev)
```

Note: `[project.dependencies]` is **not** touched by this feature — it stays `[]` (Constitution Principle I).

**Structure Decision**: Extend the existing single-package library layout (unchanged from feature 001) rather than adding a new module. The two Pydantic hook classmethods and their small validator helper are added directly inside `_base.py` alongside `_Currency`'s other cross-cutting behavior, each importing `pydantic_core` lazily inside its own body rather than at module scope — see research.md for the deferred-import rationale and for why a separate `_pydantic.py` module was considered and rejected as unwarranted for this amount of code. One new cross-cutting test file (`test_pydantic.py`) mirrors the existing per-concern test split (`test_btc.py`, `test_usd.py`, `test_errors.py`).

## Complexity Tracking

No constitution violations were identified — this section is not applicable.
