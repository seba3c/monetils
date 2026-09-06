# Quickstart: Pydantic v2 Model Field Support

**Feature**: 002-pydantic-model-support | **Spec**: [spec.md](spec.md) | **Data model**: [data-model.md](data-model.md) | **Contract**: [contracts/pydantic_integration.md](contracts/pydantic_integration.md)

These scenarios assume the feature is implemented and `pydantic` has been added as a dependency (`uv sync` after `pyproject.toml` is updated per tasks.md).

## Prerequisites

```bash
uv sync
```

## Validate: use BTC/USD directly as model fields (User Story 1)

```bash
uv run python -c "
from pydantic import BaseModel
from monetils import BTC, USD

class Invoice(BaseModel):
    price: USD
    fee: BTC

inv = Invoice(price=19.99, fee='0.5')
print(inv.price, type(inv.price).__name__)   # -> 19.99 USD
print(inv.fee, type(inv.fee).__name__)       # -> 0.50000000 BTC
"
```

Expected: both fields hold real `USD`/`BTC` instances constructed exactly as `USD(19.99)`/`BTC('0.5')` would (FR-002).

## Validate: serialize a model with BTC/USD fields (User Story 2)

```bash
uv run python -c "
from pydantic import BaseModel
from monetils import BTC, USD

class Invoice(BaseModel):
    price: USD
    fee: BTC

inv = Invoice(price=19.99, fee=1)
dumped = inv.model_dump()
print(type(dumped['price']).__name__)   # -> USD (python mode: instance itself, FR-005)

json_str = inv.model_dump_json()
print(json_str)                         # -> {\"price\":\"19.99\",\"fee\":\"1.00000000\"}  (FR-006)

restored = Invoice.model_validate_json(json_str)
print(restored == inv)                  # -> True (round-trip, FR-006/SC-004)
"
```

## Validate: standard ValidationError on invalid input (User Story 3)

```bash
uv run python -c "
from pydantic import BaseModel, ValidationError
from monetils import BTC, USD

class Invoice(BaseModel):
    fee: BTC

try:
    Invoice(fee=USD(1))   # wrong currency
except ValidationError as e:
    print('rejected:', e.error_count(), 'error(s)')   # -> rejected: 1 error(s)
"
```

Expected: a standard `pydantic.ValidationError` naming the `fee` field — never an unhandled `CurrencyMismatchError` (FR-004).

## Validate: JSON Schema generation (FR-007)

```bash
uv run python -c "
from pydantic import BaseModel
from monetils import USD

class Invoice(BaseModel):
    price: USD

import json
print(json.dumps(Invoice.model_json_schema(), indent=2))
"
```

Expected: succeeds with no error; the `price` property is described with `\"type\": \"string\"`.
