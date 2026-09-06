# Research: Pydantic v2 Model Field Support

**Feature**: 002-pydantic-model-support | **Date**: 2026-09-05

No `[NEEDS CLARIFICATION]` markers remain in the spec — the `/speckit-clarify` session pinned down the minimum supported Pydantic version, and the initial `/speckit-specify` session pinned down JSON serialization precision. This document records the implementation-level decisions needed to turn that design into code.

## Decision: use Pydantic's custom-type protocol (`__get_pydantic_core_schema__`) on `_Currency`, not an `Annotated[...]` wrapper

**Rationale**: FR-001 requires `BTC`/`USD` to work as a bare field annotation (`amount: USD`) with "no wrapper or adapter type required." Pydantic v2's officially supported mechanism for a fully custom third-party type is a `__get_pydantic_core_schema__` classmethod defined on the type itself (stable since Pydantic 2.0, satisfying the `pydantic>=2.0,<3` floor from `/speckit-clarify`). Defining it once on the private `_Currency` base means `BTC` and `USD` — and any future currency built on the same base (per feature 001's extensibility design) — inherit it automatically with zero additional code.

**Alternatives considered**:
- `Annotated[BTC, BeforeValidator(...), PlainSerializer(...)]` per-field wrapper — rejected: every model author would have to remember and repeat the wrapper, directly violating FR-001's "no wrapper required."
- A separate Pydantic-specific "field type" class (e.g. `PydanticBTC`) distinct from `BTC` — rejected: reintroduces exactly the kind of parallel-type surface the spec explicitly rules out; the feature description asks for `BTC`/`USD` themselves to be usable, not a stand-in type.

## Decision: keep the two hook methods and their validator helper inside `_base.py`, not a new `_pydantic.py` module

**Rationale**: The full implementation is two short classmethods (`__get_pydantic_core_schema__`, `__get_pydantic_json_schema__`) plus one small private validation helper — on the order of 20-25 lines. `_base.py` is already the home for all of `_Currency`'s cross-cutting behavior (storage, conversion, formatting, arithmetic, comparison, registry); Pydantic support is one more cross-cutting behavior of the same kind, not a distinct subsystem. Splitting it into its own module would add an import indirection with no corresponding reduction in complexity.

**Alternatives considered**: A dedicated `_pydantic.py` module housing the schema-building helpers, imported into `_base.py` — rejected as premature separation for this little code; can be revisited later if Pydantic-specific logic grows substantially (e.g. once a second serialization concern appears).

## Decision: validation logic — same-class passthrough, constructor delegation, uniform `ValueError` translation

**Rationale**: The validator (wired in via `core_schema.no_info_plain_validator_function`) must satisfy FR-002/FR-003/FR-004 with one function:

1. If `value` is already an instance of the exact field class (e.g. a `BTC` for a `BTC` field), return it unchanged — preserves full internal `raw` precision with zero re-parsing (FR-003), including sub-satoshi millisatoshi amounts.
2. Otherwise, attempt `cls(value)` — the *existing* constructor already accepts `int | float | Decimal | str` and interprets it in the currency's base unit (FR-002), so no parsing logic is duplicated.
3. Any exception from step 2 (a different-currency `_Currency` instance reaching the constructor's internal `Decimal(str(value))` and raising `decimal.InvalidOperation`; a wrong-currency instance failing type coercion; a `TypeError` from an unsupported input type) is caught and re-raised as a plain `ValueError` with a short message naming the field's currency class.

This matters because `CurrencyMismatchError`/`MonetilsError` extend `Exception`, not `ValueError`/`TypeError`/`AssertionError` — the only exception types Pydantic-core automatically converts into a `pydantic.ValidationError` inside a plain validator function. Left untranslated, a wrong-currency instance would crash model construction with an unhandled `MonetilsError` instead of the standard `ValidationError` FR-004 requires. Translating uniformly to `ValueError` (rather than special-casing `CurrencyMismatchError` vs. other failures) keeps the validator a single, easily tested branch.

**Alternatives considered**:
- Letting `CurrencyMismatchError` propagate directly — rejected: fails FR-004's explicit requirement for a standard `pydantic.ValidationError`, and would crash instead of producing a field-level error.
- Re-implementing base-unit parsing inside the validator instead of delegating to `cls(value)` — rejected: duplicates FR-002's constructor logic in a second place that could drift out of sync.

## Decision: serialization uses `plain_serializer_function_ser_schema(str, when_used="json")`, no custom Python-mode branch

**Rationale**: FR-005 (Python-mode dump returns the instance itself) and FR-006 (JSON-mode dump/JSON string uses the existing `str()` fixed-decimal convention) map directly onto Pydantic-core's built-in `when_used="json"` serializer option: when a serializer is registered only for the `"json"` case, Python-mode dumps fall back to returning the raw value unchanged with no extra code. This is documented Pydantic v2 behavior for exactly this "different representation per dump mode" need, present since the 2.0 custom-types protocol.

**Alternatives considered**: A single serializer function with an `info.mode` branch (`general_plain_serializer_function_ser_schema` with `info_arg=True`) — rejected: strictly more code for the same outcome as the built-in `when_used="json"` shortcut.

## Decision: JSON Schema via `__get_pydantic_json_schema__` returning a string schema

**Rationale**: FR-007 requires `model_json_schema()` to describe a `BTC`/`USD` field as a string, without custom schema code from the model author. Implementing `__get_pydantic_json_schema__(schema, handler)` to return `handler(core_schema.str_schema())` (optionally with an `examples` entry built from `str(cls(1))`) is Pydantic's documented pattern for a custom type whose JSON representation differs from its Python representation.

**Alternatives considered**: Leaving JSON Schema generation to Pydantic's default handling of `no_info_plain_validator_function` (which produces an unhelpful/opaque schema) — rejected: fails FR-007's requirement that schema generation succeed with a meaningful (string) type.

## Decision: `pydantic_core` is imported lazily, inside each hook method's body — not at `_base.py` module scope

**Rationale**: A later scope correction (via `/speckit-clarify`-adjacent user feedback after `/speckit-analyze`) reversed the original decision to add `pydantic` as a runtime dependency, in favor of keeping Constitution Principle I (Zero Runtime Dependencies) fully intact and treating `pydantic` as test/development-only (FR-009, FR-010). This is achievable because Pydantic's custom-type protocol is duck-typed: Pydantic itself does `getattr(source_type, "__get_pydantic_core_schema__", None)` when it encounters a type annotation, and only calls it if present. `_Currency` can define these methods without `pydantic`/`pydantic_core` being importable at `monetils` import time, as long as the *body* of each method — not the module — does `from pydantic_core import core_schema`. Since Pydantic only ever calls these hooks when a consumer is actively building a `pydantic.BaseModel`, that consumer necessarily already has `pydantic`/`pydantic_core` installed as their own dependency by that point — the lazy import inside the hook will always succeed in the only context where it's ever reached.

**Alternatives considered**:
- Module-level `from pydantic_core import core_schema` at the top of `_base.py` (the original design) — rejected: makes `import monetils` itself fail with `ModuleNotFoundError` for any consumer who doesn't have `pydantic` installed, which is exactly the runtime dependency Constitution Principle I forbids.
- A module-level `try/except ImportError` guard that conditionally defines the hooks only if `pydantic_core` is importable — rejected as unnecessary: since the hooks are simply never *called* unless Pydantic itself looks them up (which only happens for a consumer who has `pydantic` installed), there's no failure mode to guard against by making the method definitions themselves conditional; a plain local import inside each method is simpler and achieves the same result.

## Decision: prove FR-010 ("`import monetils` works with no `pydantic` installed") via a dedicated `tox` environment, not a `sys.modules` test trick

**Rationale**: The project's own test suite depends on `pydantic` (test/dev dependency, FR-009) to exercise the Pydantic-facing behavior, so a normal `pytest` run can't demonstrate "this also works with `pydantic` absent" — `pydantic` is always present in that environment. Monkeypatching `sys.modules["pydantic_core"] = None` inside a unit test only proves the *test process* can tolerate a missing module after the fact, not that a genuinely clean install behaves correctly at real import time, and fights the module-caching/import-machinery in ways that are fragile and easy to get subtly wrong. A separate `tox` environment that installs `monetils` without the `test` extra's `pydantic` and runs the suite minus `tests/test_pydantic.py` is a faithful, low-complexity re-creation of "a consumer who hasn't installed pydantic."

**Alternatives considered**: `unittest.mock.patch.dict(sys.modules, {"pydantic_core": None})` around an `import monetils` call inside a normal test — rejected as more fragile and less representative than an actual clean-environment `tox` run, for a check that only needs to happen occasionally (CI), not on every local `pytest` invocation.

## Risk: confirm the `pydantic>=2.0,<3` floor against the actual APIs used

**Rationale**: `pydantic` is not yet a project dependency (this is a planning artifact; no environment currently has it installed). The APIs referenced above (`__get_pydantic_core_schema__`, `core_schema.no_info_plain_validator_function`, `plain_serializer_function_ser_schema(..., when_used="json")`, `__get_pydantic_json_schema__`) are all documented as part of Pydantic's custom-types protocol since its 2.0 release, but this should be explicitly re-confirmed once `pydantic` is installed (tasks.md should include running the test suite against the floor version, e.g. via a dedicated `tox`/CI job pinning `pydantic==2.0.*`, not just against whatever latest 2.x `uv sync` resolves).

**Alternatives considered**: Skipping floor-version verification and only testing against latest `pydantic` — rejected: the whole point of declaring `>=2.0` (per `/speckit-clarify`) is that 2.0 itself is supported; an untested floor is not a verified one.

## Testing and tooling: no change beyond adding `pydantic`

`pytest` + `pytest-cov` (`fail_under = 90`, already configured), run via `uv run pytest`; `tox` across Python 3.11/3.12/3.13. The only new dependency needed for this design is `pydantic>=2.0,<3` itself — test/development-only, per the deferred-import decision above — listed under `[project.optional-dependencies].test` and `[dependency-groups].dev` per FR-009.
