# Data Model: Pydantic v2 Model Field Support

**Feature**: 002-pydantic-model-support | **Date**: 2026-09-05

Derived from spec.md's Key Entities section and the decisions in research.md. This feature adds behavior to the existing `_Currency` base (feature 001) rather than introducing new domain entities.

## `_Currency` (private abstract base) — additions

All members below are new; everything else about `_Currency` (from feature 001) is unchanged.

| Member | Signature | Behavior |
|---|---|---|
| `__get_pydantic_core_schema__` | `classmethod(source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema` | Imports `pydantic_core.core_schema` locally, inside this method (not at module scope — FR-010), then returns `core_schema.no_info_plain_validator_function(cls._pydantic_validate, serialization=core_schema.plain_serializer_function_ser_schema(str, when_used="json"))`. Registers this class as a Pydantic-recognized custom type (FR-001). |
| `__get_pydantic_json_schema__` | `classmethod(schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue` | Also imports `pydantic_core.core_schema` locally (FR-010). Returns `handler(core_schema.str_schema())` (with an `examples` entry derived from `str(cls(1))`). Makes `model_json_schema()` describe the field as a string (FR-007). |
| `_pydantic_validate` | `classmethod(value: object) -> Self` | The validator function wired into the core schema above. See "Validation behavior" below. |

## Validation behavior (`_pydantic_validate`)

| Input | Result |
|---|---|
| An instance of the exact field class (e.g. a `BTC` for a `BTC` field) | Returned unchanged — no re-parsing, no precision loss (FR-003). |
| A plain `int`/`float`/`Decimal`/numeric `str` | `cls(value)` — identical interpretation to the existing constructor: value is in the currency's base unit (FR-002). |
| An instance of a *different* `_Currency` subclass (e.g. a `USD` instance for a `BTC` field) | `ValueError` raised (translated from the constructor's failure to interpret it as a number) → Pydantic wraps it in a `ValidationError` naming the field (FR-004). |
| A value that cannot be interpreted as a number (unparseable string, `None` on a non-optional field, an unsupported type) | `ValueError` raised (translated from `decimal.InvalidOperation`/`TypeError`) → `ValidationError` naming the field (FR-004). |

## Serialization behavior

| Dump mode | Output for a `BTC`/`USD` field |
|---|---|
| Python (`model_dump()`, default mode) | The `BTC`/`USD` instance itself, unchanged (FR-005). |
| JSON (`model_dump_json()`, or `model_dump(mode="json")`) | `str(instance)` — the existing fixed-decimal convention: 2 decimal places for `USD`, 8 for `BTC` (FR-006). A `BTC` value with a sub-satoshi (millisatoshi) remainder is rounded to 8 places at this step, same as any other `str()` call. |

## JSON Schema shape

`model_json_schema()` for a `BTC`/`USD` field produces a standard string schema entry, e.g.:

```json
{"type": "string", "examples": ["1.00000000"]}
```

(USD fields use a `USD(1)`-derived example, e.g. `"1.00"`.) No custom schema code is required from the model author (FR-007).

## Dependency footprint

`pydantic` is a test/development dependency only (FR-009) — never added to `[project.dependencies]`. Because both hook methods import `pydantic_core` inside their own bodies rather than at module scope, `import monetils` and all direct (non-Pydantic) `BTC`/`USD` usage succeed with zero third-party runtime dependencies installed (FR-010); the import only executes in the environment of a consumer who is actively building a `pydantic.BaseModel`, where `pydantic`/`pydantic_core` are necessarily already present as *their* dependency.

## Relationships

- `BTC` and `USD` (feature 001) inherit all of the above unchanged from `_Currency` — no per-currency Pydantic code.
- A `pydantic.BaseModel` subclass defined by a library consumer is not part of `monetils`; it is the external entity this feature makes compatible with `BTC`/`USD` fields. No new public symbol is exported from `monetils/__init__.py` for this (FR-008).
