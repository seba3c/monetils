<div align="center">
  <h1>monetils</h1>
  <div>
    <img src="https://github.com/seba3c/monetils/actions/workflows/tests.yml/badge.svg" alt="Tests">
    <img src="https://img.shields.io/badge/coverage-100%25-brightgreen" alt="Coverage">
    <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
    <img src="https://img.shields.io/pypi/v/monetils?include_prereleases=true" alt="PyPI">
    <img src="https://img.shields.io/pypi/v/monetils?include_prereleases=true&pypi_base=https://test.pypi.org/simple&label=testpypi" alt="TestPyPI">
  </div>
  <em>A utility library for representing monetary amounts in Python.</em>
</div>

## Installation

```bash
pip install monetils
```

## Usage

`monetils` provides `BTC` and `USD` classes for representing monetary amounts exactly,
without floating-point rounding artifacts.

### Construction and formatting

```python
from monetils import BTC, USD

usd = USD(1234.5)
print(str(usd))  # "1234.50"

btc = BTC(1)
print(str(btc))  # "1.00000000"

# Construct from a non-default unit
half_btc = BTC.sat(50_000_000)
print(str(half_btc))  # "0.50000000"

nineteen_ninety_nine = USD.cent(1999)
print(str(nineteen_ninety_nine))  # "19.99"
```

### Arithmetic

```python
from monetils import BTC, USD, CurrencyMismatchError

total = USD(10.50) + USD(5.25)  # USD(15.75)

# A plain number used with +/- is treated as an amount in the currency's base unit
one_more_btc = BTC(1) + 1  # BTC(2)

# A plain number used with */÷ is a dimensionless scaling factor
doubled = BTC(1) * 2  # BTC(2)

# Mixing currencies raises CurrencyMismatchError instead of a silent wrong result
try:
    BTC(1) + USD(1)
except CurrencyMismatchError:
    print("rejected as expected")
```

### Unit conversion

```python
from monetils import BTC

one_btc = BTC(1)
one_btc.to("sat")  # Decimal("100000000")
one_btc.sats  # 100000000

msat_value = one_btc.to("msat")
BTC.msat(msat_value) == one_btc  # True — lossless round trip
```

## License

This project is licensed under the terms of the [MIT](./LICENSE) license.
