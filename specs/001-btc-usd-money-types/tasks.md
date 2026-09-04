---

description: "Task list template for feature implementation"
---

# Tasks: BTC and USD Money Representations

**Input**: Design documents from `/specs/001-btc-usd-money-types/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/public_api.md, quickstart.md (all present)

**Tests**: Included. The project constitution (Principle II, NON-NEGOTIABLE) requires new behavior to be covered by tests in `tests/` with `src/monetils` coverage ≥90% before a change is done.

**Organization**: Tasks are grouped by user story (spec.md) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- File paths are relative to the repository root

## Path Conventions

Single-package library: `src/monetils/`, `tests/` at the repository root (per plan.md's Project Structure).

---

## Phase 1: Setup

**Purpose**: Prepare the new source layout; confirm the existing toolchain baseline still works.

- [X] T001 [P] Create empty module skeletons (module-level docstring only) at src/monetils/_errors.py, src/monetils/_base.py, src/monetils/_btc.py, src/monetils/_usd.py
- [X] T002 [P] Verify baseline: `uv sync` completes and `uv run pytest` passes against the existing tests/test_placeholder.py before any implementation begins

**Checkpoint**: New module files exist; environment confirmed working.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the private, currency-agnostic engine (`_Currency`, `Unit`, the exception hierarchy) that `BTC` and `USD` both extend. Per data-model.md, this is where FR-002, FR-005, FR-006, FR-007, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014 actually live — `BTC`/`USD` (built in later phases) only add their own `units` table and per-unit classmethods.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. `_Currency` cannot be instantiated directly (it's abstract), so none of this phase's behavior is directly testable until a concrete subclass exists in Phase 3 — that's expected.

- [X] T003 [P] Implement the `Unit` frozen dataclass (`name: str`, `symbol: str`, `exponent: int`, `on_chain: bool = True`) in src/monetils/_base.py
- [X] T004 [P] Implement `MonetilsError(Exception)` and `CurrencyMismatchError(MonetilsError)` in src/monetils/_errors.py (FR-014)
- [X] T005 Implement `_Currency.__new__` (raise `TypeError` if `cls is _Currency` — FR-002), `_Currency.__init__` (value + optional `unit` → `raw: int`, rounding to the nearest whole unit at the currency's finest-unit boundary via `Decimal.quantize(..., ROUND_HALF_EVEN)` — FR-006, research.md), and `_Currency.__init_subclass__` (registers `cls.base_unit` → `cls` in the shared `_registry` dict — FR-015/FR-016) in src/monetils/_base.py (depends on: T003)
- [X] T006 Implement `_Currency.from_raw(raw: int)` classmethod (FR-005) and `_Currency.get(code: str)` classmethod (FR-015, registry lookup) in src/monetils/_base.py (depends on: T005)
- [X] T007 Implement `_Currency.to(unit: str | None = None) -> Decimal` conversion method — exact power-of-ten `Decimal` math, defaults to `base_unit` (FR-007) — in src/monetils/_base.py (depends on: T005)
- [X] T008 Implement `_Currency.__str__` (fixed decimal places from the finest **on-chain** unit only, no symbol, no thousands grouping — FR-009) and `_Currency.__repr__` (`f"{self} {self.base_unit}"`) in src/monetils/_base.py (depends on: T007)
- [X] T009 Implement `_Currency.__eq__`, `__lt__`, `__le__`, `__gt__`, `__ge__` — same-class comparison on `raw`; raise `CurrencyMismatchError` when compared against a different currency class (FR-013, FR-014) — in src/monetils/_base.py (depends on: T005, T004)
- [X] T010 Implement `_Currency.__add__`, `__sub__` (same-class → add/subtract `raw`, FR-010; plain number → treat as an amount in `base_unit`, FR-011; different currency class → `CurrencyMismatchError`, FR-014) and `__mul__`, `__truediv__` (plain number only, dimensionless scaling factor rounded per FR-006, FR-012; division by zero → builtin `ZeroDivisionError`) in src/monetils/_base.py (depends on: T005, T004)

**Checkpoint**: Foundation ready — `BTC`/`USD` can now be defined as thin subclasses.

---

## Phase 3: User Story 1 - Represent and format a monetary amount (Priority: P1) 🎯 MVP

**Goal**: A developer can construct a `BTC` or `USD` amount directly and get a correctly formatted `str()`.

**Independent Test**: Construct `BTC(1)`, `USD(1234.5)`, and `BTC(0.5)`; call `str()` on each and confirm the fixed-precision output (spec User Story 1, acceptance scenarios 1-3 — using `BTC(0.5)` in place of the spec's `BTC.sat(50_000_000)` example so this story doesn't depend on Phase 5's per-unit classmethods; both construct an equal value).

### Tests for User Story 1 ⚠️

> Write these first — they must fail (`BTC`/`USD` don't exist yet) before the implementation tasks below.

- [X] T011 [P] [US1] Write `BTC` construction + `str()`/`repr()` tests (`BTC(1)` → `"1.00000000"`, `BTC(0.5)` → `"0.50000000"`, `BTC(-1)`, `BTC(0)` → `"0.00000000"`) in tests/test_btc.py
- [X] T012 [P] [US1] Write `USD` construction + `str()`/`repr()` tests (`USD(1234.5)` → `"1234.50"`, `USD(-5)`, `USD(0)` → `"0.00"`) in tests/test_usd.py

### Implementation for User Story 1

- [X] T013 [P] [US1] Define the `BTC` class, with a full public docstring (class + `__init__`), in src/monetils/_btc.py: extends `_Currency`, `base_unit = "BTC"`, full `units` table (`BTC` exp 0, `mBTC` exp -3, `sat` exp -8, `msat` exp -11 `on_chain=False`) (depends on: T003, T005, T007, T008, T009, T010; Constitution Development Workflow — public-behavior changes require docstrings in the same change)
- [X] T014 [P] [US1] Define the `USD` class, with a full public docstring (class + `__init__`), in src/monetils/_usd.py: extends `_Currency`, `base_unit = "USD"`, full `units` table (`USD` exp 0, `cent` exp -2) (depends on: T003, T005, T007, T008, T009, T010; Constitution Development Workflow — public-behavior changes require docstrings in the same change)
- [X] T015 [US1] Export `BTC`, `USD`, `MonetilsError`, `CurrencyMismatchError` from src/monetils/__init__.py, setting `__all__ = ["BTC", "USD", "MonetilsError", "CurrencyMismatchError"]` explicitly (so T024 can verify the export surface); bump `__version__` there and `version` in pyproject.toml from `"0.2.0"` to `"0.3.0"` (Constitution Principle V — additive public API, MINOR bump) (depends on: T013, T014, T004)

**Checkpoint**: User Story 1 is fully functional and independently testable — `uv run pytest tests/test_btc.py tests/test_usd.py -k "not (Arith or Convert)"` style scoping aside, `BTC`/`USD` construct and format correctly on their own.

---

## Phase 4: User Story 2 - Perform arithmetic and comparisons on amounts safely (Priority: P2)

**Goal**: `+`, `-`, `*`, `/`, and comparisons work correctly between same-currency instances and between an instance and a plain number, and reject `BTC`/`USD` mixing.

**Note**: The operators themselves were already implemented generically in Phase 2 (T009, T010) — this phase has no new *implementation* tasks, only tests that exercise that shared logic through the concrete `BTC`/`USD` classes delivered in Phase 3. That is itself a meaningful check: it's the first point at which per-currency specifics (each currency's own `raw` rounding boundary) actually run.

**Independent Test**: `USD(10.50) + USD(5.25) == USD(15.75)`; `BTC(1) + 1 == BTC(2)`; `BTC(1) * 2 == BTC(2)`; `BTC(1) + USD(1)` raises `CurrencyMismatchError`.

### Tests for User Story 2 ⚠️

- [X] T016 [P] [US2] Add BTC arithmetic + comparison tests to tests/test_btc.py: same-class `+`/`-`, plain-number `+`/`-` as an amount (`BTC(1) + 1 == BTC(2)`), `*`/`/` as a scaling factor (`BTC(1) * 2 == BTC(2)`), division producing a fractional millisatoshi rounds to nearest (`BTC.from_raw(10) / 3`), division by zero raises `ZeroDivisionError`, and `==`/`<`/`<=`/`>`/`>=` between two `BTC` instances (depends on: T013)
- [X] T017 [P] [US2] Add USD arithmetic + comparison tests to tests/test_usd.py: same shape as T016, scoped to USD/cents (depends on: T014)
- [X] T018 [P] [US2] Write cross-currency rejection tests in tests/test_errors.py: `BTC(1) + USD(1)`, `BTC(1) - USD(1)`, and comparing a `BTC` to a `USD` each raise `CurrencyMismatchError` (spec Edge Cases, FR-014) (depends on: T013, T014, T004)

**Checkpoint**: User Stories 1 and 2 both work independently; cross-currency mixing is verified to fail safely.

---

## Phase 5: User Story 3 - Convert an amount between units of the same currency (Priority: P3)

**Goal**: Convert a `BTC`/`USD` amount to any of its recognized units (`.to(unit)`, or a convenience property) and reconstruct from a non-default unit, without loss of value on a round trip.

**Independent Test**: `BTC(1).to("msat") == 100_000_000_000`; `BTC.msat(100_000_000_000) == BTC(1)`; `BTC(1).sats == 100_000_000`; `USD.cent(1999)` formats as `"19.99"`.

### Tests for User Story 3 ⚠️

- [X] T019 [P] [US3] Add BTC unit-conversion tests to tests/test_btc.py: `.to("sat")`, `.to("mBTC")`, `.to("msat")`, `.sats` property, `BTC.mBTC(...)`/`BTC.sat(...)`/`BTC.msat(...)` classmethods, round-trip via `.to("msat")` + `BTC.msat(...)` + `.from_raw()`, and excess-precision rounding at the millisatoshi boundary (depends on: T013)
- [X] T020 [P] [US3] Add USD unit-conversion tests to tests/test_usd.py: `.to("cent")`, `.cents` property, `USD.cent(...)` classmethod, round-trip via `.from_raw()`, and excess-precision rounding at the cent boundary (e.g. `USD(1.005)`) (depends on: T014)
- [X] T021 [P] [US3] Add unrecognized-unit-name tests to tests/test_errors.py: `BTC(1).to("euro")` and `BTC(1, unit="euro")` each raise builtin `KeyError` (spec Edge Cases) (depends on: T013)

### Implementation for User Story 3

- [X] T022 [P] [US3] Implement `BTC.mBTC(value)`, `BTC.sat(value)`, `BTC.msat(value)` classmethods (each delegates to `BTC(value, unit=...)`, hand-written per currency rather than dynamically generated — research.md, Constitution Principle III) and the `.sats` property (`int(self.to("sat"))`), each with a docstring, in src/monetils/_btc.py (depends on: T013, T007; Constitution Development Workflow — docstrings)
- [X] T023 [P] [US3] Implement `USD.cent(value)` classmethod and the `.cents` property (`int(self.to("cent"))`), each with a docstring, in src/monetils/_usd.py (depends on: T014, T007; Constitution Development Workflow — docstrings)

**Checkpoint**: All three user stories are independently functional. Full feature (FR-001 through FR-016) is implemented.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify the remaining spec-level guarantees that cut across all stories, and close out constitution requirements.

- [X] T024 [P] Add tests to tests/test_errors.py: instantiating the private base directly (`from monetils._base import _Currency; _Currency(1)`) raises builtin `TypeError` (FR-002, spec Edge Cases); `BTC.get("USD") is USD` and `USD.get("BTC") is BTC` (FR-015); and the public export surface is exactly `{"BTC", "USD", "MonetilsError", "CurrencyMismatchError"}` (e.g. `import monetils; assert set(monetils.__all__) == {...}` and/or `assert not hasattr(monetils, "_Currency")`) (FR-001, SC-007)
- [X] T025 Run `uv run ruff check --fix .` and `uv run ruff format .` across all new/changed files
- [X] T026 Run `uv run pytest --cov=src/monetils` and confirm coverage stays at or above 90% (Constitution Principle II); add any tests needed to close gaps. Confirm tests/test_btc.py and tests/test_usd.py each pass when run in isolation (`uv run pytest tests/test_btc.py` / `tests/test_usd.py` alone), demonstrating the currency-test isolation SC-006 relies on
- [X] T027 Manually execute every `uv run python -c "..."` scenario in quickstart.md and confirm the printed output matches what's documented
- [X] T028 [P] Update README.md with a short "Usage" section documenting `BTC`/`USD` construction, arithmetic, `str()` formatting, and unit conversion (Constitution Development Workflow: public-behavior changes must update README.md in the same change)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup (T001) — BLOCKS all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion. No dependency on other stories.
- **User Story 2 (Phase 4)**: Depends on Foundational + User Story 1 (needs concrete `BTC`/`USD` to exist — T013/T014). Independently testable on its own once US1 is done.
- **User Story 3 (Phase 5)**: Depends on Foundational + User Story 1 (same reason as US2). Independent of US2.
- **Polish (Phase 6)**: Depends on all three user stories being complete.

### Within Each Phase

- Tests are written before the implementation tasks in the same phase and must fail first.
- `_base.py` tasks in Phase 2 are sequential (same file, each builds on the last); `_errors.py` (T004) and `_base.py`'s `Unit` dataclass (T003) can run in parallel with each other.
- Within Phase 3/4/5, `_btc.py` and `tests/test_btc.py` work is independent of `_usd.py` and `tests/test_usd.py` work — mirror currencies can be built in parallel.

### Parallel Opportunities

- T001 and T002 (Setup) in parallel.
- T003 and T004 (Foundational) in parallel; T005–T010 are sequential (same file).
- Within Phase 3: T011 ∥ T012 (tests), then T013 ∥ T014 (implementation), then T015.
- Within Phase 4: T016 ∥ T017 ∥ T018 (three different test files).
- Within Phase 5: T019 ∥ T020 ∥ T021 (tests), then T022 ∥ T023 (implementation).
- T024 and T028 (Polish) can run in parallel with each other; T025–T027 are sequential (each depends on the codebase state left by the previous).

---

## Parallel Example: User Story 1

```bash
# Tests first (different files):
Task: "Write BTC construction + str()/repr() tests in tests/test_btc.py"
Task: "Write USD construction + str()/repr() tests in tests/test_usd.py"

# Then implementation (different files):
Task: "Define the BTC class in src/monetils/_btc.py"
Task: "Define the USD class in src/monetils/_usd.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup) and Phase 2 (Foundational) — Foundational is the larger effort here since it holds all the currency-agnostic logic.
2. Complete Phase 3 (User Story 1).
3. **STOP and VALIDATE**: `uv run pytest tests/test_btc.py tests/test_usd.py` — construction and formatting work independently.
4. This is a legitimate MVP: a consumer can already `from monetils import BTC, USD` and get correctly represented, formatted amounts.

### Incremental Delivery

1. Setup + Foundational → engine ready (nothing usable yet — `_Currency` is private and abstract).
2. + User Story 1 → **MVP**: construct and format `BTC`/`USD`.
3. + User Story 2 → safe arithmetic and comparisons, cross-currency mixing rejected.
4. + User Story 3 → full unit-conversion surface (`to()`, per-unit classmethods, `.sats`/`.cents`).
5. + Polish → coverage gate, lint/format clean, README updated, quickstart re-verified end-to-end.

## Notes

- [P] tasks touch different files with no unmet dependency.
- Every arithmetic/comparison/formatting behavior lives once in `_Currency` (Phase 2); `BTC`/`USD` (Phase 3) are thin — a `units` table plus, in Phase 5, a few hand-written per-unit classmethods. This is what makes FR-016 (new currency without touching existing ones) true in practice: a future currency is a new `_xyz.py` module plus one import line in `__init__.py`.
- Commit after each task or logical group; stop at any checkpoint to validate a story independently.
