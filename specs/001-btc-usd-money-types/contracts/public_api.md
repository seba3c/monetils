# Public API Contract: monetils

**Feature**: 001-btc-usd-money-types (regenerated after spec redesign)

`monetils` is a library, not a network or CLI service — its "contract" is the public symbols exported from `src/monetils/__init__.py` and their documented behavior.

## Exports

```python
from monetils import BTC, USD
from monetils import MonetilsError, CurrencyMismatchError
```

Nothing else is part of the public interface — no shared base class, no `Unit` type (FR-001, SC-007).

### `BTC`

```python
class BTC:
    def __init__(self, value: int | float | Decimal | str, unit: str | None = None) -> None: ...
    # unit defaults to "BTC". Rounds to the nearest millisatoshi if `value`
    # carries more precision than that (FR-006).

    @classmethod
    def mBTC(cls, value: int | float | Decimal | str) -> "BTC": ...
    @classmethod
    def sat(cls, value: int | float | Decimal | str) -> "BTC": ...
    @classmethod
    def msat(cls, value: int | float | Decimal | str) -> "BTC": ...
    @classmethod
    def from_raw(cls, raw: int) -> "BTC": ...
    @classmethod
    def get(cls, code: str) -> type["BTC"] | type["USD"]: ...

    raw: int          # millisatoshi count (FR-006)

    @property
    def sats(self) -> int: ...  # == int(self.to("sat"))

    def to(self, unit: str | None = None) -> Decimal: ...  # defaults to "BTC"

    def __str__(self) -> str: ...    # e.g. "1.00000000" — 8 places, no symbol (FR-009)
    def __repr__(self) -> str: ...   # e.g. "1.00000000 BTC"

    def __add__(self, other: "BTC | int | float | Decimal") -> "BTC": ...
    def __sub__(self, other: "BTC | int | float | Decimal") -> "BTC": ...
    def __mul__(self, scalar: int | float | Decimal) -> "BTC": ...
    def __truediv__(self, scalar: int | float | Decimal) -> "BTC": ...
    def __eq__(self, other: object) -> bool: ...
    def __lt__(self, other: "BTC") -> bool: ...
    def __le__(self, other: "BTC") -> bool: ...
    def __gt__(self, other: "BTC") -> bool: ...
    def __ge__(self, other: "BTC") -> bool: ...
```

### `USD`

```python
class USD:
    def __init__(self, value: int | float | Decimal | str, unit: str | None = None) -> None: ...
    # unit defaults to "USD".

    @classmethod
    def cent(cls, value: int | float | Decimal | str) -> "USD": ...
    @classmethod
    def from_raw(cls, raw: int) -> "USD": ...
    @classmethod
    def get(cls, code: str) -> type["BTC"] | type["USD"]: ...

    raw: int          # cent count (FR-006)

    @property
    def cents(self) -> int: ...  # == int(self.to("cent"))

    def to(self, unit: str | None = None) -> Decimal: ...  # defaults to "USD"

    def __str__(self) -> str: ...    # e.g. "19.99" — 2 places, no symbol (FR-009)
    def __repr__(self) -> str: ...   # e.g. "19.99 USD"

    # Same operator set as BTC, scoped to USD.
```

Preconditions / postconditions common to both classes:

- `+` / `-` / comparisons: same-class operand → correctly valued/ordered result on `raw` (FR-010, FR-013). Plain-number operand with `+`/`-` → treated as an amount in the class's base unit (FR-011). Operand of the *other* currency class → `CurrencyMismatchError` (FR-014).
- `*` / `/`: operand is always a plain number, treated as a dimensionless scaling factor, never a currency amount (FR-012). Division by zero → builtin `ZeroDivisionError`.
- `.to(unit)` / a constructor's `unit=`: an unrecognized unit name → builtin `KeyError` (not a `MonetilsError`).
- Instantiating the private shared base directly is not reachable through this public surface at all (it isn't exported); attempting it via an internal import raises builtin `TypeError` (FR-002).

### Exceptions

- `MonetilsError(Exception)` — base class; never raised directly.
- `CurrencyMismatchError(MonetilsError)` — FR-014.

## Backward compatibility

The package currently exports nothing beyond `__version__`. This feature adds only new public symbols (`BTC`, `USD`, `MonetilsError`, `CurrencyMismatchError`) — no existing export changes. Per Constitution Principle V this is a MINOR version bump (`0.2.0` → `0.3.0`).

`Currency.get(code)`'s return type (`type[BTC] | type[USD]`) will need to grow its union the next time a currency is added (research.md) — noted here so that future work doesn't miss it.
