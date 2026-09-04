# Data Model: BTC and USD Money Representations

**Feature**: 001-btc-usd-money-types | **Date**: 2026-09-04 (regenerated after spec redesign)

Derived from spec.md's Key Entities section, the Clarifications session (including the two reference implementations), and the decisions in research.md.

## `_Currency` (private abstract base)

Not part of the public interface (FR-001). Cannot be instantiated directly — `_Currency(...)` raises `TypeError` (FR-002, research.md). Implements everything currency-agnostic; `BTC` and `USD` supply only their own `units` table and per-unit classmethods.

| Member | Type | Description |
|---|---|---|
| `raw` | `int` (public instance attribute) | Value as a whole number of the currency's finest recognized unit (FR-006) |
| `units` | `dict[str, Unit]` (class attribute, defined per subclass) | All recognized units for the currency, keyed by name |
| `base_unit` | `str` (class attribute, defined per subclass) | The default unit's key into `units` |
| `_registry` | `dict[str, type]` (class attribute, shared) | Maps `base_unit` → currency class, populated as `BTC`/`USD` are defined (FR-015, FR-016) |

Methods (implemented once, inherited by `BTC`/`USD`):

| Member | Signature | Behavior |
|---|---|---|
| `__init__` | `(value: int \| float \| Decimal \| str, unit: str \| None = None)` | `unit` defaults to `base_unit`; computes `raw` from `value` expressed in `unit`, rounding to the nearest whole `raw` unit if `value` carries excess precision (FR-006) |
| `from_raw` | `classmethod(raw: int) -> Self` | Reconstructs an instance directly from its raw integer (FR-005) |
| `to` | `(unit: str \| None = None) -> Decimal` | Exact conversion to `unit` (defaults to `base_unit`) (FR-007) |
| `get` | `classmethod(code: str) -> type[BTC] \| type[USD]` | Registry lookup by currency code (FR-015); see research.md for why the return type is an explicit union rather than `type[_Currency]` |
| `__str__` | `() -> str` | Fixed-convention formatted string: no symbol/code, no grouping, decimal places from the currency's finest **on-chain** unit (FR-009) |
| `__repr__` | `() -> str` | `f"{self} {self.base_unit}"`, e.g. `"1.00000000 BTC"` |
| `__eq__` | `(other) -> bool` | `type(self) is type(other) and self.raw == other.raw` |
| `__lt__`, `__le__`, `__gt__`, `__ge__` | `(other) -> bool` | Same-class ordering comparisons on `raw` (FR-013); raise `CurrencyMismatchError` if `type(other) is not type(self)` and `other` is a `_Currency` instance of a different currency |
| `__add__`, `__sub__` | `(other) -> Self` | Same-class: add/subtract `raw` (FR-010). Plain number: treat as an amount in `base_unit`, convert, then add/subtract (FR-011). Different currency class: raise `CurrencyMismatchError` (FR-014) |
| `__mul__`, `__truediv__` | `(scalar) -> Self` | `scalar` is a dimensionless multiplier/divisor (never an amount) applied to `raw`, rounding to the nearest whole `raw` unit (FR-012, FR-006). Division by zero raises the builtin `ZeroDivisionError` |

## `Unit` (private, internal)

Not separately importable. One instance per recognized unit, held in a currency class's `units` dict.

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Unit name (`"BTC"`, `"mBTC"`, `"sat"`, `"msat"`, `"USD"`, `"cent"`) |
| `symbol` | `str` | Display symbol, carried for completeness/future use — not currently rendered anywhere (`str()` omits it per FR-009) |
| `exponent` | `int` | Power of ten relative to the currency's base unit (`BTC`=0, `mBTC`=-3, `sat`=-8, `msat`=-11; `USD`=0, `cent`=-2) |
| `on_chain` | `bool` (default `True`) | Whether this unit ever settles on-chain; `False` for `msat` only. Excluded from `str()`'s decimal-place calculation (FR-009) but still counts toward storage precision (FR-006) |

## `BTC` (public)

Extends `_Currency`. `base_unit = "BTC"`. `units`: `BTC` (exp 0), `mBTC` (exp -3), `sat` (exp -8), `msat` (exp -11, `on_chain=False`).

| Member | Signature | Notes |
|---|---|---|
| `BTC(value, unit=None)` | constructor | `unit` defaults to `"BTC"` (FR-003) |
| `BTC.mBTC(value)` | classmethod → `BTC` | FR-004 |
| `BTC.sat(value)` | classmethod → `BTC` | FR-004 |
| `BTC.msat(value)` | classmethod → `BTC` | FR-004 |
| `.sats` | property → `int` | `int(self.to("sat"))` (FR-008) |

Display: 8 decimal places (finest on-chain unit = satoshi). Storage: millisatoshi precision.

## `USD` (public)

Extends `_Currency`. `base_unit = "USD"`. `units`: `USD` (exp 0), `cent` (exp -2, `on_chain=True`).

| Member | Signature | Notes |
|---|---|---|
| `USD(value, unit=None)` | constructor | `unit` defaults to `"USD"` (FR-003) |
| `USD.cent(value)` | classmethod → `USD` | FR-004 |
| `.cents` | property → `int` | `int(self.to("cent"))` (FR-008, inferred by symmetry — see spec Assumptions) |

Display: 2 decimal places. Storage: cent precision.

## Errors

| Type | Extends | Raised when |
|---|---|---|
| `MonetilsError` | `Exception` | Base class for all library-specific errors; never raised directly |
| `CurrencyMismatchError` | `MonetilsError` | An arithmetic or comparison operation is attempted between a `BTC` and a `USD` instance (FR-014) |

Builtin exceptions used deliberately, *not* wrapped: `TypeError` for instantiating `_Currency` directly (FR-002); `KeyError` for an unrecognized unit name passed to `.to()` or a constructor's `unit=` (spec Edge Cases); `ZeroDivisionError` for division by zero.

## Relationships

```text
_Currency (private, abstract) ──┬── BTC (public)
                                 └── USD (public)

BTC.units, USD.units:  dict[str, Unit]     (Unit is private, not shared across currencies)
_Currency._registry:   dict[str, type]     (shared; populated by both BTC and USD)
```

No entity has a lifecycle or state transitions — `BTC`, `USD`, and `Unit` are all conventionally-immutable value objects (research.md), created once and not mutated after construction.
