# Implementation Plan: BTC and USD Money Representations

**Branch**: `001-btc-usd-money-types` | **Date**: 2026-09-04 (regenerated after spec redesign) | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-btc-usd-money-types/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Add `BTC` and `USD` classes to `monetils` for representing bitcoin and US-dollar amounts. Both extend a private, non-instantiable `_Currency` base that implements all currency-agnostic behavior: integer storage at each currency's finest recognized unit (millisatoshi for BTC, cent for USD), a generic `.to(unit)` conversion method, auto-derived-but-hand-typed per-unit classmethod constructors (`BTC.sat(...)`, `BTC.mBTC(...)`, `BTC.msat(...)`, `USD.cent(...)`), fixed-precision `str()` formatting based on each currency's finest on-chain-settling unit (8 places for BTC, 2 for USD), same-class and plain-number arithmetic, same-class comparisons, and a `.get(code)` currency registry. Only `BTC`, `USD`, `MonetilsError`, and `CurrencyMismatchError` are part of the public interface — stdlib only (`decimal`, `dataclasses`), no runtime dependencies, per Constitution Principle I. Cross-currency arithmetic/comparison raises `CurrencyMismatchError`; instantiating the private base raises builtin `TypeError`; an unrecognized unit name raises builtin `KeyError`.

## Technical Context

**Language/Version**: Python 3.11+ (already the project's `requires-python` floor; CI matrix covers 3.11, 3.12, 3.13)

**Primary Dependencies**: None at runtime — stdlib only (`decimal`, `dataclasses`). Existing dev/test tooling (`pytest`, `pytest-cov`, `ruff`, `tox`) is unchanged.

**Storage**: N/A — `BTC`, `USD`, and the private `_Currency`/`Unit` types are in-memory value objects; nothing is persisted.

**Testing**: `pytest` + `pytest-cov` via `uv run pytest --cov=src/monetils` (coverage gate already set to `fail_under = 90` in `pyproject.toml`); `tox` runs the suite across the Python 3.11/3.12/3.13 matrix.

**Target Platform**: Any OS running a supported CPython version; distributed as a pure-Python wheel via PyPI/TestPyPI.

**Project Type**: Single-package library (existing `src/monetils/` layout) — no CLI, service, or UI component.

**Performance Goals**: Not performance-critical. Correctness (exact-value arithmetic, no silent precision loss) takes priority over throughput; no specific ops/sec target.

**Constraints**: Zero runtime dependencies (Constitution I); fully typed public API, `py.typed` retained (Constitution III) — this specifically rules out the reference implementation's dynamic `setattr`-based classmethod generation; see research.md. Must pass `ruff check` / `ruff format --check` under the existing rule set (Constitution IV).

**Scale/Scope**: 2 currency classes at launch (BTC: 4 units; USD: 2 units), designed so a future currency is added as its own class without touching `BTC`/`USD` (FR-016). Stateless, conventionally-immutable value types — no concurrency or data-volume constraints.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Zero Runtime Dependencies | PASS | Design uses only stdlib (`decimal`, `dataclasses`); no new entry in `[project.dependencies]`. |
| II. Test-First & High Coverage | PASS (enforced at implementation) | New behavior lands with tests in `tests/`; `tasks.md` must keep `src/monetils` coverage ≥90% across Python 3.11–3.13. |
| III. Typed Public API | PASS (with an explicit adaptation) | The reference implementation's dynamic `setattr`-generated classmethods are reimplemented as hand-written, fully typed classmethods per currency (research.md) specifically to satisfy this principle — same runtime behavior, visible to static type checkers. |
| IV. Lint & Format Enforcement | PASS | No change to `pyproject.toml` `[tool.ruff]` config; new code must pass the existing rule set as-is. |
| V. Semantic Versioning | PASS (MINOR bump) | Package currently exports only `__version__`; this feature is purely additive public API (`BTC`, `USD`, `MonetilsError`, `CurrencyMismatchError`) — bump `0.2.0` → `0.3.0`, no MAJOR-level break. |

No violations — see Complexity Tracking below. The Typed-API adaptation is a design choice made *to satisfy* Constitution III, not a deviation from it, so it does not need a Complexity Tracking justification entry.

## Project Structure

### Documentation (this feature)

```text
specs/001-btc-usd-money-types/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md          # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── public_api.md     # Phase 1 output (/speckit-plan command)
├── checklists/
│   └── requirements.md    # Spec quality checklist (/speckit-specify, /speckit-clarify)
└── tasks.md                # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/monetils/
├── __init__.py     # Public exports: BTC, USD, MonetilsError, CurrencyMismatchError
├── _base.py         # Private _Currency abstract base + Unit dataclass: raw storage, to(), from_raw(),
│                     # get()/registry, __str__/__repr__, arithmetic and comparison operators
├── _btc.py            # BTC class: units table, mBTC()/sat()/msat() classmethods, .sats property
├── _usd.py             # USD class: units table, cent() classmethod, .cents property
├── _errors.py            # MonetilsError, CurrencyMismatchError
└── py.typed               # (existing)

tests/
├── __init__.py             # (existing)
├── test_btc.py               # BTC construction, units, arithmetic, conversion, formatting
├── test_usd.py                 # USD construction, units, arithmetic, conversion, formatting
└── test_errors.py                # CurrencyMismatchError, abstract-base TypeError, unrecognized-unit KeyError, registry lookup
```

**Structure Decision**: Single-package library layout (template Option 1, simplified — no `models/`/`services/`/`cli/` subfolders, since this is a pure value-type library rather than a service or CLI). The shared logic lives in a private `_base.py` so that `_btc.py` and `_usd.py` each stay small and currency-specific (supports FR-016: a third currency is a new `_xyz.py` module plus one new import line in `__init__.py`, no edits to `_btc.py`/`_usd.py`/`_base.py`). `tests/` mirrors the per-currency split plus one file for cross-cutting error behavior.

## Complexity Tracking

No constitution violations were identified — this section is not applicable.
