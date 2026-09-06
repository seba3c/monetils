---

description: "Task list template for feature implementation"
---

# Tasks: Pydantic v2 Model Field Support

**Input**: Design documents from `/specs/002-pydantic-model-support/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/pydantic_integration.md, quickstart.md (all present)

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

**Purpose**: Confirm the pre-change baseline, then add the new test/development-only dependency this feature requires (never a runtime one — FR-009, FR-010).

- [X] T001 Verify baseline: `uv run pytest` passes against the existing test suite (tests/test_btc.py, tests/test_usd.py, tests/test_errors.py) before any change begins
- [X] T002 Add `pydantic>=2.0,<3` to `[project.optional-dependencies].test` and to `[dependency-groups].dev` in pyproject.toml (FR-009) — do **not** add it to `[project.dependencies]` (Constitution Principle I; FR-010 requires `import monetils` to keep working without `pydantic` installed); run `uv sync` to install it (depends on: T001)

**Checkpoint**: `pydantic` is installed and importable; existing tests still pass unmodified.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement Pydantic v2 compatibility once on the private, shared `_Currency` base (feature 001) so `BTC` and `USD` both inherit it automatically with no per-currency code. Per data-model.md and research.md, this is where FR-001 through FR-007, and FR-010's lazy-import mechanism, actually live — the user story phases below only add tests that exercise this shared implementation through the concrete `BTC`/`USD` classes.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Implement `_Currency._pydantic_validate(cls, value)` classmethod in src/monetils/_base.py: return `value` unchanged if `isinstance(value, cls)` (exact-class passthrough, preserves full precision — FR-003); if `isinstance(value, _Currency)` but NOT `isinstance(value, cls)` (a different currency's instance), raise `ValueError` immediately — do **not** fall through to `cls(value)`, since `_Currency.__str__` returns a plain numeric string that `Decimal(str(value))` would otherwise silently accept as a valid amount (research.md); otherwise attempt `cls(value)`, catching `(TypeError, ValueError, ArithmeticError)` (covers `decimal.InvalidOperation`, which is an `ArithmeticError`) and re-raising as `ValueError` naming `cls.__name__` (FR-002, FR-004) (depends on: T002)
- [X] T004 Implement `_Currency.__get_pydantic_core_schema__(cls, source_type, handler)` classmethod in src/monetils/_base.py: import `pydantic_core.core_schema` **locally inside this method** (`from pydantic_core import core_schema`), not at module scope — `_base.py` must remain importable with `pydantic` absent (FR-010); return `core_schema.no_info_plain_validator_function(cls._pydantic_validate, serialization=core_schema.plain_serializer_function_ser_schema(str, when_used="json"))` — registers `_Currency` subclasses as Pydantic-recognized types with python-mode identity dumps (FR-005) and JSON-mode `str()` dumps (FR-006) (depends on: T003)
- [X] T005 Implement `_Currency.__get_pydantic_json_schema__(cls, schema, handler)` classmethod in src/monetils/_base.py: import `pydantic_core.core_schema` locally inside this method too (same reasoning as T004, FR-010); return `handler(core_schema.str_schema())` with an added `examples` entry derived from `str(cls(1))`, so `model_json_schema()` describes the field as a string (FR-007) (depends on: T004)

**Checkpoint**: Foundation ready — `BTC` and `USD` are now usable directly as Pydantic v2 model fields with no further code changes.

---

## Phase 3: User Story 1 - Use BTC/USD directly as a Pydantic model field type (Priority: P1) 🎯 MVP

**Goal**: A developer annotates a Pydantic model field as `BTC` or `USD` and successfully builds an instance from a plain number, numeric string, or existing instance.

**Independent Test**: Define a model with a `USD` field and a `BTC` field, construct it from `{"amount": 19.99}` / `{"amount": "0.5"}` / an existing instance, and confirm each field holds the correctly valued instance (spec User Story 1, acceptance scenarios 1-3).

### Tests for User Story 1 ⚠️

> Write these first — they exercise the Foundational implementation through concrete `BTC`/`USD` fields for the first time.

- [X] T006 [US1] Write tests in tests/test_pydantic.py: a `BaseModel` with `USD`/`BTC` fields constructs correctly from an `int`/`float`/`str` value (base-unit interpretation, matching `USD(value)`/`BTC(value)` — FR-002) and from an existing same-class instance without precision loss (FR-003); an optional `BTC | None` field accepts and stores `None`; `model_json_schema()` succeeds for a model with both field types and describes each as a JSON string property (FR-007) (depends on: T005)

**Checkpoint**: User Story 1 is fully functional and independently testable — `uv run pytest tests/test_pydantic.py` passes for construction and schema generation.

---

## Phase 4: User Story 2 - Serialize a model containing BTC/USD fields (Priority: P2)

**Goal**: `model_dump()` and `model_dump_json()` produce the documented representation for `BTC`/`USD` fields, and a JSON round-trip reproduces the original value.

**Independent Test**: Construct a model with `BTC`/`USD` fields, call `model_dump()` and `model_dump_json()`, and confirm the output matches FR-005/FR-006; re-validate the JSON output and confirm equality with the original (spec User Story 2, acceptance scenarios 1-4).

**Note**: Serialization was already implemented in Phase 2 (T004) as part of the same core schema as validation — this phase adds no new implementation, only tests that exercise it.

### Tests for User Story 2 ⚠️

- [X] T007 [US2] Write tests in tests/test_pydantic.py: `model_dump()` (python mode) returns the `USD`/`BTC` instance itself unchanged (FR-005); `model_dump_json()` and `model_dump(mode="json")` return the fixed-decimal `str()` convention for both currencies (2 places USD, 8 places BTC — FR-006); constructing a new model instance from the dumped JSON reproduces the original value (SC-004) (depends on: T005; same file as T006 — run after it, not in parallel)

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Get clear, standard validation errors on invalid input (Priority: P3)

**Goal**: Invalid input to a `BTC`/`USD` field (wrong currency, unparseable value, disallowed `None`) raises a standard `pydantic.ValidationError` naming the field — never a raw `monetils` exception.

**Independent Test**: Construct a model with a `BTC` field using a `USD` instance, and separately using an unparseable string; confirm both raise `pydantic.ValidationError` naming the field (spec User Story 3, acceptance scenarios 1-3).

**Note**: Error translation was already implemented in Phase 2 (T003) — this phase adds no new implementation, only tests.

### Tests for User Story 3 ⚠️

- [X] T008 [US3] Write tests in tests/test_pydantic.py: a `BTC` field given a `USD` instance (and vice versa) raises `pydantic.ValidationError` naming the field (FR-004, the silent-string-coercion pitfall covered by T003); a `USD`/`BTC` field given an unparseable string, and a required (non-optional) field given `None`, each raise `pydantic.ValidationError` naming the field; assert no `MonetilsError`/`CurrencyMismatchError` ever escapes model construction (SC-003) (depends on: T005; same file as T006/T007 — run after them, not in parallel)

**Checkpoint**: All three user stories are independently functional. Full feature (FR-001 through FR-010) is implemented.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify remaining spec-level guarantees, including the zero-runtime-dependency property this feature depends on.

- [X] T009 [P] Run `uv run ruff check --fix .` and `uv run ruff format .` across all new/changed files
- [X] T010 Run `uv run pytest --cov=src/monetils` and confirm coverage stays at or above 90% (Constitution Principle II); add any tests needed to close gaps (depends on: T006, T007, T008)
- [X] T011 Confirm the declared `pydantic>=2.0,<3` floor actually works: verify (via a dedicated `tox` environment/CI job pinning `pydantic==2.0.*`, or a scratch virtualenv install) that `__get_pydantic_core_schema__`, `core_schema.no_info_plain_validator_function`, `plain_serializer_function_ser_schema(..., when_used="json")`, and `__get_pydantic_json_schema__` behave as implemented on the floor version, not just on whatever latest 2.x `uv sync` resolves (research.md risk) — verified against `pydantic==2.0.3` in a scratch venv (Python 3.11): all 17 tests/test_pydantic.py tests pass unmodified
- [X] T012 Manually execute every `uv run python -c "..."` scenario in quickstart.md and confirm the printed output matches what's documented — all four ran and matched exactly
- [X] T013 [P] Update README.md with a short "Pydantic support" section documenting `amount: USD` / `amount: BTC` field annotation, accepted input, `model_dump()`/`model_dump_json()` behavior, and JSON schema generation (Constitution Development Workflow: public-behavior changes must update README.md in the same change) — also updated `BTC`/`USD` class docstrings to mention Pydantic field support (closes the docstring gap `/speckit-analyze` flagged as D1)
- [X] T014 Add a `tox` environment (alongside the existing 3.11/3.12/3.13 envs) that installs `monetils` without the `test` extra's `pydantic` and runs `uv run pytest tests/ --ignore=tests/test_pydantic.py`, proving `import monetils` and all direct (non-Pydantic) `BTC`/`USD` behavior work with zero third-party runtime dependencies installed (FR-010, research.md) — ran `tox -e no-pydantic`: confirmed `pydantic` genuinely absent from that venv (`ModuleNotFoundError`) and all 62 non-Pydantic tests pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup (T002, `pydantic` installed) — BLOCKS all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion. No dependency on other stories.
- **User Story 2 (Phase 4)**: Depends on Foundational completion. Shares tests/test_pydantic.py with US1 — run after T006 to avoid conflicting edits, but has no logical dependency on US1's test content.
- **User Story 3 (Phase 5)**: Depends on Foundational completion. Same file-ordering note as US2.
- **Polish (Phase 6)**: Depends on all three user stories being complete.

### Within Each Phase

- Tests are written before/alongside the (already-complete) implementation they exercise and must pass against Phase 2's implementation.
- `_base.py` tasks in Phase 2 are sequential (same file, each builds on the last).
- T006, T007, T008 all append to the same file (tests/test_pydantic.py) — run sequentially, not in parallel, to avoid conflicting edits; none of them logically depends on the others' content.

### Parallel Opportunities

- T009 (lint/format) and T013 (README) touch different files from each other and from T010-T012, and can run in parallel once all three user stories are complete.
- No cross-story parallelism is available in this feature the way it was in feature 001 (BTC/USD-per-file split) — all three stories share one shared implementation point (`_Currency`) and one shared test file.

---

## Parallel Example: Polish Phase

```bash
# Once all user stories are complete, these can run together:
Task: "Run uv run ruff check --fix . and uv run ruff format . across all new/changed files"
Task: "Update README.md with a short Pydantic support section"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — implements the entire feature; blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (`uv run pytest tests/test_pydantic.py`)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → full feature implementation ready, unverified by story-specific tests
2. Add User Story 1 tests → verify independently → MVP demonstrated
3. Add User Story 2 tests → verify independently → serialization demonstrated
4. Add User Story 3 tests → verify independently → error handling demonstrated
5. Polish: lint/format, coverage, floor-version check, quickstart validation, README, no-pydantic tox environment

### Parallel Team Strategy

Because Phase 2 (Foundational) implements the entire feature in one shared location (`_Currency`) and every user story tests through the same file (tests/test_pydantic.py), this feature is naturally sequential for one contributor rather than split-by-story-per-developer. If multiple contributors are available, split by Polish task (T009, T011, T013) after Phase 5 completes instead.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- T003's ordering (explicit different-currency check before generic construction) is the single most important correctness detail in this feature — verify T008's test actually fails without it before trusting it passes because of it
- T004/T005's local (not module-level) `pydantic_core` import is the second most important correctness detail — verify T014's no-pydantic tox environment actually fails if either import is moved to module scope, before trusting it passes because of it
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
