# Feature Specification: BTC and USD Money Representations

**Feature Branch**: `001-btc-usd-money-types`

**Created**: 2026-09-04

**Status**: Draft

**Input**: User description: "Python utility library that provides representations for BTC and USD currencies, formating and typical math operations. Eventually the library will support other currencies. It also support currency units conversions such as BTC as mSAT or USD to cents"

## Clarifications

### Session 2026-09-04

- Q: When a caller creates an amount with more decimal precision than its currency's smallest unit supports (e.g. a USD amount specified to 5 decimal places, or a BTC amount specified to 9 decimal places), what should happen? → A: Round to the nearest smallest unit automatically (same policy as FR-010's arithmetic rounding).
- Q: For this feature, should the formatted display use one fixed convention, or should the API let callers configure the display (locale, separators, symbol vs. code, decimal-place count)? → A: Single fixed display convention for v1; configurable/locale-aware formatting is out of scope for this feature.
- Q: When an operation is rejected (cross-currency arithmetic, invalid unit conversion, etc.), should the library raise its own dedicated exception type(s), or is raising standard built-in exceptions (TypeError/ValueError) sufficient? → A: Dedicated exception type(s) specific to monetils.
- Q: What is the standard number of decimal places used in each currency's fixed formatted display? → A: USD displays 2 decimal places; BTC displays 6 decimal places. *(Superseded below — see the 8-decimal-place answer later in this session.)*
- Q: What should the public library interface look like? → A: Only `BTC` and `USD` (plus the exception types) are importable; any shared base implementation is private and cannot be instantiated directly. Amounts are constructed positionally in the currency's default unit — `BTC(1)` is 1 BTC, `USD(1)` is 1 USD. Arithmetic operators accept either another same-currency instance or a plain number. Unit conversion and construction were originally sketched as named methods (`.to_msat()`, `.from_msats(...)`) — see below for the design that superseded this.
- Q: You said `BTC(1)` represents 1 BTC, but also that `str(BTC(1))` returns `"0.000001"` — which is right? → A: `BTC(1)` is 1 whole BTC; the formatted string carries no currency symbol or code (a plain number).
- Q: A full reference implementation was provided (abstract `Currency` base; `BTC`/`USD` root currencies; per-unit auto-generated classmethod constructors; generic `.to(unit)` conversion) whose own test asserted `str(BTC(1)) == "1.00000000"` (8 decimal places) — conflicting with the 2-decimal/6-decimal answer above. Which is correct? → A: 8 decimal places for BTC (matches satoshi precision and the reference code/tests); USD stays at 2 decimal places.
- Q: The same reference implementation raises plain built-in `TypeError` for both instantiating the abstract base directly and for cross-currency arithmetic (`BTC(1) + USD(1)`) — conflicting with the earlier "dedicated exception type" answer. Which should the library actually raise? → A: Keep the dedicated `CurrencyMismatchError` (a `MonetilsError` subclass) for cross-currency arithmetic/comparison; plain built-in `TypeError` only for attempting to instantiate the private abstract base directly (that case is a generic "you can't do that," not a currency-domain error).
- Q: An initial version of the reference implementation defined standalone unit subclasses (`SAT`, `MSAT`, `MBTC`, `USD_CENT`) instantiable directly and satisfying `isinstance(SAT(...), BTC)`. A revised reference implementation removed them, replacing them with auto-generated per-unit classmethod constructors on `BTC`/`USD` that return plain `BTC`/`USD` instances (e.g. `BTC.sat(...)` returns a `BTC`, not a `SAT`). → A: Adopt the revised design — no standalone unit subclasses; only `BTC` and `USD` (plus exception types) are part of the public interface, matching the earlier "everything else must be private" requirement.
- Q: The reference implementation's `__add__` only accepts another instance of the exact same class, so `BTC(1) + 1` would raise `TypeError` under that code (`1` is a plain `int`, not a `BTC`) — conflicting with the very first requirement that `BTC(1) + 1` should equal `BTC(2)`. Which is correct? → A: Keep plain-number `+`/`-` support: `BTC(1) + 1` still equals `BTC(2)` (the number is treated as an amount in the currency's default unit), on top of same-class `+`/`-`. The reference code's strict same-type check applies only between two *different* currency classes (that's what triggers `CurrencyMismatchError`).
- Q: (Consolidated integration of the final reference implementation) → A: The design now follows the second reference implementation closely: a private abstract `_Currency` base (not exported; raises `TypeError` if instantiated directly) implements all currency-agnostic logic. `BTC` and `USD` are its only public subclasses. Each currency defines a `units` table (name, power-of-ten exponent relative to the base unit, and an `on_chain` flag — `False` for units that never settle on-chain, e.g. BTC's millisatoshi). Internal storage (`raw: int`, a public attribute) is an integer count of the currency's *finest recognized unit* (millisatoshi for BTC, cent for USD) — this supersedes the earlier "satoshi is BTC's precision boundary" assumption; a `.from_raw(raw)` classmethod reconstructs an instance directly from that integer. One classmethod constructor is auto-generated per non-base unit (e.g. `BTC.mBTC(...)`, `BTC.sat(...)`, `BTC.msat(...)`, `USD.cent(...)`), each returning a plain instance of that currency class. Conversion is a generic `.to(unit_name)` method (returns an exact `Decimal`, defaulting to the base unit); `BTC` additionally exposes a `.sats` convenience property (int), and `USD` an equivalent `.cents` property by the same pattern (not explicitly shown in the reference code, but a direct extension of it — flagged here as inferred rather than confirmed verbatim). `str()` formats to a fixed number of decimal places determined by the currency's finest **on-chain-settling** unit only (BTC: satoshi → 8 places; USD: cent → 2 places) — so display precision (8 places) is coarser than storage precision (11 places, millisatoshi) for BTC. The formatted string has no currency symbol/code and no thousands-separator grouping (inferred from the reference code's plain `f"{value:.{places}f}"` format — no `,` grouping flag is present; this supersedes the earlier "symbol + grouped decimal" assumption). Each currency class also inherits a `.get(code)` lookup against a shared internal registry, returning the registered currency class for a given code (e.g. `BTC.get("USD")` returns `USD`) — this is what makes FR-016's future-currency extensibility automatic once a new currency class is defined. Requesting an unrecognized unit name (via `.to(...)` or a constructor's `unit=` argument) is not given a dedicated exception in the reference code; it is left to raise the plain built-in `KeyError` from the internal unit-table lookup.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Represent and format a monetary amount (Priority: P1)

A developer using the library creates a monetary amount by instantiating `BTC` or `USD` directly and obtains a correctly formatted, human-readable string via `str()`.

**Why this priority**: This is the foundation every other capability depends on — without a core amount representation and a way to display it, arithmetic and conversion have nothing to operate on or report through.

**Independent Test**: Construct a `BTC` and a `USD` instance and call `str()` on each; verify the output matches the currency's fixed decimal-place convention.

**Acceptance Scenarios**:

1. **Given** `USD(1234.5)`, **When** `str()` is called on it, **Then** the result is `"1234.50"` (2 decimal places, no thousands separator, no currency symbol).
2. **Given** `BTC(1)`, **When** `str()` is called on it, **Then** the result is `"1.00000000"` (8 decimal places, no currency symbol).
3. **Given** `BTC.sat(50_000_000)`, **When** `str()` is called on it, **Then** the result is `"0.50000000"` (the equivalent whole/fractional BTC amount).

---

### User Story 2 - Perform arithmetic and comparisons on amounts safely (Priority: P2)

A developer adds, subtracts, multiplies, divides, and compares `BTC` or `USD` instances — using either another instance of the same class or a plain number — and the library prevents accidentally mixing `BTC` and `USD` while producing mathematically correct, precision-aware results.

**Why this priority**: Arithmetic is the second most fundamental capability — required for any real bookkeeping or calculation use — but it builds on the amount representation established in User Story 1.

**Independent Test**: Perform each supported operation (add, subtract, multiply, divide, compare) using both same-class operands and plain-number operands; attempt an operation across `BTC` and `USD` and confirm it is rejected.

**Acceptance Scenarios**:

1. **Given** `USD(10.50)` and `USD(5.25)`, **When** they are added, **Then** the result equals `USD(15.75)`.
2. **Given** `BTC(1)`, **When** `1` is added to it, **Then** the result equals `BTC(2)` (a plain number used with `+`/`-` is interpreted as an amount in the currency's default unit).
3. **Given** `BTC.sat(50_000_000)` and `BTC(0.5)`, **When** they are compared for equality, **Then** they are equal (same underlying value regardless of which unit constructed them).
4. **Given** `BTC(1)` and `USD(1)`, **When** addition is attempted between them, **Then** a `CurrencyMismatchError` is raised instead of a result.
5. **Given** `BTC.msat(10)`, **When** it is divided by 3, **Then** the result rounds to the nearest whole millisatoshi (the storage precision boundary).
6. **Given** `BTC(1)`, **When** it is multiplied by 2, **Then** the result equals `BTC(2)` (a plain number used with `*`/`/` is a dimensionless scaling factor, not an amount to add).

---

### User Story 3 - Convert an amount between units of the same currency (Priority: P3)

A developer converts a `BTC` or `USD` amount to one of its recognized units using `.to(unit)` (or a convenience property), and constructs an amount from a non-default unit using an auto-generated classmethod, without loss of value on a round trip.

**Why this priority**: Unit conversion adds real value but is layered on top of the representation and arithmetic from User Stories 1-2; a user already gets value from the library without it, but not the reverse.

**Independent Test**: Convert a `BTC` amount with `.to("msat")`, reconstruct it with `BTC.msat(...)`, and confirm the value is unchanged; repeat for `USD`/cents.

**Acceptance Scenarios**:

1. **Given** `BTC(1)`, **When** `.to("sat")` is called, **Then** the result is `100_000_000`.
2. **Given** `BTC(1)`, **When** its `.sats` property is accessed, **Then** the result is `100_000_000` (an `int`, equivalent to `.to("sat")`).
3. **Given** `USD.cent(1999)`, **When** `str()` is called on it, **Then** the result is `"19.99"`.
4. **Given** `BTC(1)`, **When** it is converted with `.to("msat")` and reconstructed via `BTC.msat(...)` using that result, **Then** the reconstructed instance equals the original `BTC(1)`.

---

### Edge Cases

- Creating a negative amount (e.g. `BTC(-1)`, `USD(-5.00)`) is permitted (see Assumptions), to represent debits, refunds, or differences.
- Creating or converting an amount with more decimal precision than the currency's finest recognized unit supports (millisatoshi for BTC, cent for USD) rounds the value to the nearest such unit (FR-006).
- Dividing an amount by zero raises an error rather than returning a result.
- An arithmetic or comparison operation attempted between a `BTC` instance and a `USD` instance raises `CurrencyMismatchError` (FR-014), rather than silently producing a result.
- Attempting to instantiate the private shared base implementation directly (rather than through `BTC`/`USD`) raises a plain built-in `TypeError` (FR-002) — not a `MonetilsError`, since this is a generic "you can't do that," not a currency-domain error.
- Requesting an unrecognized unit name (e.g. `.to("euro")`, or `unit="euro"` to a constructor) raises a plain built-in `KeyError` — no dedicated exception is defined for this case.
- Formatting a zero-value amount displays using the same fixed convention as any other value (e.g. `str(USD(0)) == "0.00"`, `str(BTC(0)) == "0.00000000"`).
- Very large amounts (e.g. far beyond the current BTC supply or a typical USD balance) are represented exactly, with no artificial upper bound on value.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system's importable public surface MUST consist only of the `BTC` class, the `USD` class, and the library's exception types. No generic/shared base class MUST be part of the public interface.
- **FR-002**: Attempting to instantiate the private shared base implementation directly (rather than through `BTC` or `USD`) MUST raise a plain built-in `TypeError`.
- **FR-003**: `BTC` and `USD` MUST be constructible by passing a plain numeric value in the currency's default (base) unit directly to the class (e.g. `BTC(1)` is 1 BTC; `USD(1)` is 1 USD).
- **FR-004**: Each currency class MUST provide one auto-derived classmethod constructor per additional recognized unit (e.g. `BTC.mBTC(...)`, `BTC.sat(...)`, `BTC.msat(...)`, `USD.cent(...)`), each returning a plain instance of that currency class constructed from a value expressed in that unit.
- **FR-005**: Each currency class MUST provide a `.from_raw(raw: int)` classmethod that reconstructs an instance directly from its internal integer representation (FR-006's `raw` value).
- **FR-006**: The system MUST treat each currency's finest recognized unit (millisatoshi for BTC, cent for USD) as its internal storage precision boundary: the internal value (exposed as a public `raw: int` attribute) MUST NOT silently lose amounts below that boundary, and any value or operation result that is not already a whole number of that finest unit MUST round to the nearest one.
- **FR-007**: Each currency class MUST provide a generic `.to(unit)` method that converts an instance's value to any of its recognized units by name, defaulting to the currency's base unit when no unit is given, with exact (non-lossy) conversion math.
- **FR-008**: `BTC` MUST provide a `.sats` property returning its value as an integer count of satoshis; `USD` MUST provide an equivalent `.cents` property returning its value as an integer count of cents.
- **FR-009**: Calling `str()` on an instance MUST return a fixed-convention formatted numeric string — no currency symbol or code, no thousands-separator grouping — at a decimal-place count determined by the currency's finest unit that settles **on-chain** (excluding units, like millisatoshi, that never settle on-chain): 2 decimal places for `USD` (e.g. `str(USD(19.99)) == "19.99"`), 8 decimal places for `BTC` (e.g. `str(BTC(1)) == "1.00000000"`). This display precision is independent of the finer storage precision boundary in FR-006.
- **FR-010**: `+` and `-` between two instances of the same currency class MUST produce a correctly valued result of that class.
- **FR-011**: `+` and `-` between an instance and a plain number MUST treat the number as an amount in that currency's default unit (e.g. `BTC(1) + 1` equals `BTC(2)`), producing a correctly valued result of that class.
- **FR-012**: `*` and `/` between an instance and a plain number MUST treat the number as a dimensionless scaling factor, not a currency amount, producing a correctly valued result of that class.
- **FR-013**: The system MUST support comparing two instances of the same currency class (`==`, `<`, `<=`, `>`, `>=`).
- **FR-014**: Any arithmetic or comparison operation attempted between a `BTC` instance and a `USD` instance MUST be rejected by raising a dedicated library-specific exception (`CurrencyMismatchError`), rather than silently producing an incorrect result.
- **FR-015**: Each currency class MUST provide a `.get(code)` lookup, backed by a shared internal registry, that returns the registered currency class for a given currency code (e.g. `BTC.get("USD")` returns the `USD` class).
- **FR-016**: The system MUST be structured so that a new currency can be added in a future release as its own dedicated, directly importable class following the same pattern as `BTC`/`USD` (default-unit constructor, per-unit classmethods, `.to()`, `str()` formatting), without modifying the behavior or code of existing currency classes; registering it MUST make it discoverable via `.get(code)` from any existing currency class (FR-015).

### Key Entities

- **BTC**: Public class representing an amount of bitcoin. Base unit: BTC. Other recognized units: mBTC (10⁻³ BTC, on-chain), satoshi (10⁻⁸ BTC, on-chain), millisatoshi (10⁻¹¹ BTC, Lightning-only — not on-chain). Instantiated directly (`BTC(1)`) or via `BTC.mBTC(...)` / `BTC.sat(...)` / `BTC.msat(...)`. Displays at 8 decimal places (its finest on-chain unit); stores internally at millisatoshi precision (its finest recognized unit overall).
- **USD**: Public class representing an amount of US dollars. Base unit: USD. Other recognized unit: cent (10⁻² USD, on-chain). Instantiated directly (`USD(1)`) or via `USD.cent(...)`. Displays at 2 decimal places; stores internally at cent precision.
- **(private shared base)**: Not part of the public interface; cannot be instantiated directly (FR-002). Implements all currency-agnostic logic shared by `BTC`/`USD`: `raw` storage, `.to()`, `.from_raw()`, `.get()`, `str()`/`repr()` formatting, arithmetic and comparison operators, and the shared currency registry.
- **Unit** (internal, per-currency definition — not separately importable): name, exponent (power of ten relative to the currency's base unit), and an `on_chain` flag distinguishing units that settle on-chain from ones that don't (e.g. millisatoshi). Non-on-chain units are excluded from `str()`'s decimal-place calculation (FR-009) but still count toward storage precision (FR-006) and remain usable for construction and conversion.

### Errors

- **MonetilsError**: Base class for all library-specific errors; never raised directly.
- **CurrencyMismatchError** (extends `MonetilsError`): Raised when an arithmetic or comparison operation is attempted between a `BTC` instance and a `USD` instance (FR-014).

Two situations intentionally use plain built-in exceptions instead of a `MonetilsError` subclass: instantiating the private shared base directly raises `TypeError` (FR-002), and requesting an unrecognized unit name raises `KeyError` (see Edge Cases) — neither is a currency-domain error in the sense `CurrencyMismatchError` is.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can create a monetary amount as `BTC(...)` or `USD(...)` and obtain its `str()` representation without writing any custom formatting code.
- **SC-002**: Round-trip unit conversions (via `.to()`, the auto-generated per-unit classmethods, and `.from_raw()`) return the exact original value in 100% of tested cases.
- **SC-003**: Arithmetic and comparison operations between two instances of the same currency class, or between an instance and a plain number, produce mathematically correct results, verified against reference calculations, in 100% of tested cases.
- **SC-004**: Every attempted operation between a `BTC` instance and a `USD` instance is rejected with `CurrencyMismatchError`, with zero cases of a cross-currency operation silently producing a result.
- **SC-005**: No monetary operation or conversion loses value beyond the currency's finest recognized unit (millisatoshi for BTC, cent for USD); zero floating-point rounding artifacts are observed across tested arithmetic and conversion scenarios.
- **SC-006**: A new currency can be added as its own class without modifying any existing currency class's code, and becomes discoverable via `.get(code)` from any existing currency class, verified by test isolation between currencies.
- **SC-007**: Only `BTC`, `USD`, and the library's exception types can be imported from the library's public interface; no other symbol (including any shared base implementation) is part of the importable public surface, verified by inspecting the package's exports.

## Assumptions

- Only `BTC` and `USD` are implemented in this initial feature. Additional currencies will be added in future releases as their own dedicated classes, following the same pattern (FR-016).
- Cross-currency conversion (e.g. BTC to USD) is out of scope for this feature. In a future feature, currencies will expose a conversion method that accepts a caller-supplied exchange rate value (no automatic rate lookup); this feature's design should not preclude adding that later.
- `USD`'s `.cents` property (FR-008) is inferred by symmetry with `BTC`'s `.sats` property; it was not shown verbatim in the reference implementation but follows the same demonstrated pattern.
- `str()` output has no thousands-separator grouping — inferred from the reference implementation's plain `f"{value:.{places}f}"` format string, which carries no grouping flag. This supersedes the earlier "symbol + grouped decimal" assumption from earlier in this session.
- Negative amounts are permitted and treated as valid values, to represent debits, refunds, or differences.
- The library's consumers are other Python programs (it is a utility library, not an end-user application), so "users" throughout this spec refers to developers integrating the library.
- Requesting an unrecognized unit name is treated as programmer error and surfaces the plain built-in `KeyError` from the internal unit lookup, rather than a dedicated `MonetilsError` subclass — consistent with the reference implementation, which does not special-case it.
