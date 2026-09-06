# Feature Specification: Pydantic v2 Model Field Support

**Feature Branch**: `002-pydantic-model-support`

**Created**: 2026-09-05

**Status**: Draft

**Input**: User description: "add support for pydantic, USD and BTC class can be use as pydantic model fields, only support pydantic v2. Add unitests, add pydantic dependency as runtime and test"

## Clarifications

### Session 2026-09-05

- Q: What is the minimum Pydantic v2 release monetils should guarantee support for? → A: `pydantic>=2.0,<3` — broadest compatibility, since the custom-type hook this feature relies on has been stable since Pydantic's first 2.0 release.
- Q: Should `pydantic` be a mandatory runtime dependency, or a test/development-only dependency? → A: Test/development-only. `monetils` stays zero-runtime-dependency (Constitution Principle I, fully preserved — no amendment needed); the Pydantic integration hooks defer their `pydantic_core` import to call-time so `import monetils` never requires `pydantic` to be installed. A consumer must supply their own `pydantic` installation to use `BTC`/`USD` as model fields.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Use BTC/USD directly as a Pydantic model field type (Priority: P1)

A developer defines a Pydantic model with a field typed `BTC` or `USD` (e.g. `amount: USD`) and builds an instance of that model from raw input data (a plain number, a numeric string, or an already-constructed `BTC`/`USD` instance). The model construction succeeds and the field holds a correctly valued `BTC`/`USD` instance, with no custom validator code required from the developer.

**Why this priority**: This is the entire point of the feature — without a model being able to accept `BTC`/`USD` directly as a field annotation, there is nothing else to build on.

**Independent Test**: Define a minimal Pydantic model with a `BTC` field and a `USD` field, construct it from a dict of raw values, and confirm each field is an instance of the correct currency class with the expected value.

**Acceptance Scenarios**:

1. **Given** a Pydantic model with field `amount: USD`, **When** it is constructed with `{"amount": 19.99}`, **Then** `model.amount` is `USD(19.99)`.
2. **Given** a Pydantic model with field `amount: BTC`, **When** it is constructed with `{"amount": "0.5"}`, **Then** `model.amount` is `BTC(0.5)`.
3. **Given** a Pydantic model with field `amount: BTC`, **When** it is constructed with `{"amount": BTC.sat(50_000_000)}` (an existing instance), **Then** `model.amount` equals that same instance's value with no data loss.

---

### User Story 2 - Serialize a model containing BTC/USD fields (Priority: P2)

A developer serializes a Pydantic model instance containing `BTC`/`USD` fields back to a Python dict or to JSON (`model_dump()`, `model_dump_json()`) and gets back a representation of the amount that is safe to store or transmit, without writing custom serialization code.

**Why this priority**: Serialization is the natural counterpart to validation (User Story 1) and is required for the field to be usable in real request/response and storage workflows, but a developer already gets value from validation alone.

**Independent Test**: Construct a model with `BTC`/`USD` fields, call `model_dump()` and `model_dump_json()`, and confirm the output for each field matches the documented representation.

**Acceptance Scenarios**:

1. **Given** a model with field `amount: USD` set to `USD(19.99)`, **When** `model_dump()` (Python mode) is called, **Then** `amount` in the resulting dict is the `USD(19.99)` instance itself.
2. **Given** a model with field `amount: USD` set to `USD(19.99)`, **When** `model_dump_json()` is called, **Then** the JSON value for `amount` is `"19.99"`.
3. **Given** a model with field `amount: BTC` set to `BTC(1)`, **When** `model_dump_json()` is called, **Then** the JSON value for `amount` is `"1.00000000"`.
4. **Given** the JSON produced in Scenario 3, **When** it is used to construct a new instance of the same model, **Then** the reconstructed `amount` equals the original `BTC(1)`.

---

### User Story 3 - Get clear, standard validation errors on invalid input (Priority: P3)

A developer passes invalid data to a `BTC`/`USD` model field — the wrong currency's instance, an un-parseable value, or an unsupported type — and receives a standard Pydantic `ValidationError` identifying the offending field and the problem, the same way any other Pydantic field reports invalid input.

**Why this priority**: Correct error reporting matters for a good developer experience and for integration with frameworks (e.g. FastAPI) that render `ValidationError` into a response, but the feature is usable without it if validation and serialization (User Stories 1-2) already work for valid input.

**Independent Test**: Attempt to construct models with a `USD` instance where a `BTC` field is expected, and with an unparseable string, and confirm both raise `pydantic.ValidationError` naming the field.

**Acceptance Scenarios**:

1. **Given** a Pydantic model with field `amount: BTC`, **When** it is constructed with `{"amount": USD(1)}`, **Then** a `pydantic.ValidationError` is raised naming the `amount` field (not a raw `CurrencyMismatchError`).
2. **Given** a Pydantic model with field `amount: USD`, **When** it is constructed with `{"amount": "not-a-number"}`, **Then** a `pydantic.ValidationError` is raised naming the `amount` field.
3. **Given** a Pydantic model with field `amount: USD`, **When** it is constructed with `{"amount": None}` and the field is not declared optional, **Then** a `pydantic.ValidationError` is raised naming the `amount` field.

---

### Edge Cases

- A field typed `BTC` given a plain number is interpreted the same way the `BTC(...)` constructor interprets a plain number: an amount in BTC's base unit (whole BTC), not satoshis or another unit.
- A field typed `BTC` given a `BTC` instance whose value carries sub-satoshi (millisatoshi) precision is preserved through model construction without rounding (construction only, not necessarily through JSON serialization — see FR-006).
- Generating a model's JSON Schema (e.g. via `model_json_schema()`, as used by frameworks like FastAPI for OpenAPI docs) for a `BTC`/`USD` field produces a schema entry describing the field as a numeric string, without erroring.
- A field declared `BTC | None` (optional) accepts `None` and stores it as `None`, following standard Pydantic optional-field behavior.
- Two sibling fields of different currency types on the same model (e.g. `price: USD` and `fee: BTC`) validate and serialize independently; validating one never affects or depends on the other.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `BTC` and `USD` MUST be usable directly as Pydantic v2 model field annotations (e.g. `amount: USD`, `amount: BTC | None`), including in `Optional`/union and default-value forms, with no wrapper or adapter type required.
- **FR-002**: When a model is constructed (or a field is validated) with a plain number (`int`/`float`) or a numeric string, the value MUST be validated by constructing the field's currency class the same way `BTC(value)` / `USD(value)` already does (value interpreted in the currency's base unit), producing a correctly valued instance.
- **FR-003**: When a model is constructed with a value that is already an instance of the field's exact currency class, that instance's value MUST be used without loss of precision (see also FR-006 on the storage/display precision distinction).
- **FR-004**: When a model is constructed with a value that is an instance of a *different* currency class than the field declares (e.g. a `USD` instance for a `BTC` field), or a value that cannot be interpreted as a number, validation MUST fail with a standard `pydantic.ValidationError` identifying the field — not an unhandled `CurrencyMismatchError` or other library-internal exception.
- **FR-005**: Serializing a model in Python mode (`model_dump()`) MUST return the `BTC`/`USD` instance itself, unchanged, for each such field (consistent with how Pydantic treats other rich Python value types in Python-mode dumps).
- **FR-006**: Serializing a model to JSON (`model_dump_json()`, or `model_dump(mode="json")`) MUST represent a `BTC`/`USD` field's value as the same fixed-decimal string produced by that instance's `str()` (2 decimal places for `USD`, 8 for `BTC`). Amounts finer than that display precision (i.e. `BTC` values carrying a sub-satoshi millisatoshi remainder) are rounded to that precision on JSON serialization, consistent with `str()`'s existing display-precision convention.
- **FR-007**: Generating a model's JSON Schema for a `BTC`/`USD` field (e.g. via `model_json_schema()`) MUST succeed and describe the field using a string schema, without requiring the developer to write custom schema code.
- **FR-008**: The library's Pydantic integration MUST work without modification to the existing public `BTC`/`USD`/exception API described in the prior feature (001) — no breaking change to direct (non-Pydantic) construction, arithmetic, comparison, conversion, or formatting behavior.
- **FR-009**: `pydantic` MUST NOT be added to the project's runtime dependencies — `monetils` MUST remain installable with zero third-party runtime dependencies (Constitution Principle I). `pydantic>=2.0,<3` MUST be added to the project's test dependencies and development tooling (no support commitment for Pydantic v1 or an eventual Pydantic v3) so the test suite can import and exercise it directly; a consumer who wants to use `BTC`/`USD` as Pydantic model fields MUST supply their own `pydantic` installation.
- **FR-010**: `import monetils`, and all existing direct (non-Pydantic) usage of `BTC`/`USD`, MUST succeed in an environment where `pydantic` is not installed at all. The Pydantic integration hooks MUST defer importing `pydantic`/`pydantic_core` until a consumer actually attempts to use `BTC`/`USD` as a Pydantic model field, not at `monetils` import time.

### Key Entities

- **BTC / USD**: The existing public currency classes (see feature 001). This feature adds Pydantic v2 compatibility to them; it does not change their fields, methods, or direct (non-Pydantic) behavior.
- **Pydantic model**: Any `pydantic.BaseModel` subclass defined by a developer using this library, with one or more fields annotated `BTC`, `USD`, or an optional/union/default form of either.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can annotate a Pydantic model field as `BTC` or `USD` and successfully construct, validate, and serialize model instances without writing any custom validator, serializer, or schema code.
- **SC-002**: 100% of tested valid inputs (plain numbers, numeric strings, and same-currency instances) construct a model field with the exact expected `BTC`/`USD` value.
- **SC-003**: 100% of tested invalid inputs (wrong-currency instance, unparseable value, disallowed type) result in a standard `pydantic.ValidationError` naming the offending field, with zero unhandled library-internal exceptions escaping model construction.
- **SC-004**: Round-tripping a model through `model_dump_json()` and re-validating the result reproduces the original field value in 100% of tested cases, down to the display-precision guarantee in FR-006.
- **SC-005**: `model_json_schema()` succeeds for every model containing a `BTC`/`USD` field in 100% of tested cases, with zero schema-generation errors.

## Assumptions

- Only Pydantic v2 is supported; Pydantic v1 compatibility is explicitly out of scope, per the feature description.
- Validation of a plain number/string mirrors the existing `BTC(value)`/`USD(value)` constructor exactly: the value is interpreted in the currency's base unit (whole BTC or whole USD), not a sub-unit. Constructing from a non-default unit (e.g. satoshis) through a Pydantic field requires passing an already-constructed instance (e.g. `BTC.sat(...)`), not a bare number plus a unit string.
- JSON serialization reuses the existing `str()` fixed-decimal convention (FR-006) rather than introducing a new, separate raw-integer JSON representation; this keeps the JSON shape a plain human-readable numeric string (matching how the library already presents amounts) at the cost of not preserving BTC's sub-satoshi (millisatoshi/Lightning-only) precision across a JSON round-trip. Millisatoshi precision is preserved when passing an existing in-memory instance directly between models (FR-003), just not through a JSON encode/decode cycle.
- `pydantic` is a test/development-only dependency, not a runtime one — Constitution Principle I ("Zero Runtime Dependencies") is fully preserved by this feature; no constitution amendment is required. This is achieved by deferring the `pydantic_core` import to inside the Pydantic hook methods themselves (FR-010), a standard "soft dependency" pattern — Pydantic only ever calls those hooks when a consumer (who necessarily already has `pydantic` installed as their own dependency) builds a model using `BTC`/`USD`.
- This feature covers `BTC` and `USD` only; if additional currencies are added in the future (per feature 001's extensibility design), they are expected to gain the same Pydantic support automatically since it is implemented once on the shared base, not per-currency.
- FastAPI or other framework-level integration testing is out of scope; this feature is verified at the Pydantic model level (`BaseModel` construction, dump, and schema generation) directly.
