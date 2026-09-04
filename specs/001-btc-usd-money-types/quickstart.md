# Quickstart: BTC and USD Money Representations

**Feature**: 001-btc-usd-money-types | **Spec**: [spec.md](spec.md) | **Data model**: [data-model.md](data-model.md) | **Contract**: [contracts/public_api.md](contracts/public_api.md)

## Prerequisites

```bash
uv sync
```

## Validate: create and format amounts (User Story 1)

```bash
uv run python -c "
from monetils import BTC, USD

usd = USD(1234.5)
print(str(usd))          # -> 1234.50

btc = BTC(1)
print(str(btc))          # -> 1.00000000

half_btc = BTC.sat(50_000_000)
print(str(half_btc))     # -> 0.50000000
"
```

Expected: fixed-precision numeric strings with no currency symbol and no thousands grouping (FR-009) — 2 places for USD, 8 for BTC.

## Validate: arithmetic, plain-number operands, and cross-currency rejection (User Story 2)

```bash
uv run python -c "
from monetils import BTC, USD, CurrencyMismatchError

a = USD(10.50)
b = USD(5.25)
print(str(a + b))            # -> 15.75

print(str(BTC(1) + 1))       # -> 2.00000000  (plain number = amount in BTC, FR-011)
print(str(BTC(1) * 2))       # -> 2.00000000  (plain number = scaling factor, FR-012)

try:
    BTC(1) + USD(1)
except CurrencyMismatchError:
    print('rejected as expected')
"
```

Expected: same-currency and plain-number arithmetic succeed; cross-currency addition raises `CurrencyMismatchError` (FR-014) and never reaches a result.

## Validate: unit conversion round-trip (User Story 3)

```bash
uv run python -c "
from monetils import BTC

one_btc = BTC(1)
msat_value = one_btc.to('msat')
print(msat_value)                     # -> 100000000000

back = BTC.msat(msat_value)
assert back == one_btc, 'round-trip must be lossless'
print('round-trip ok')

print(one_btc.sats)                   # -> 100000000  (convenience property, FR-008)
"
```

Expected: the round trip (BTC → millisatoshi → BTC) returns exactly the original amount (SC-002).

## Validate: registry lookup and extensibility hook (FR-015/FR-016)

```bash
uv run python -c "
from monetils import BTC, USD

assert BTC.get('USD') is USD
assert USD.get('BTC') is BTC
print('registry ok')
"
```

## Run the automated test suite

```bash
uv run pytest --cov=src/monetils
```

Expected: all tests pass; line coverage of `src/monetils` is at or above 90% (Constitution Principle II).

## Lint, format, and type checks

```bash
uv run ruff check .
uv run ruff format --check .
```

Expected: no findings (Constitution Principle IV). All public classmethods (`BTC.sat`, `BTC.mBTC`, `BTC.msat`, `USD.cent`, etc.) are hand-written and fully typed (research.md) — no dynamically-injected attributes that would be invisible to a type checker (Constitution Principle III).
