# Contract: Pydantic v2 Model Field Support

**Feature**: 002-pydantic-model-support

`monetils` is a library; this feature adds no new importable public symbol (no change to `from monetils import BTC, USD, MonetilsError, CurrencyMismatchError`). Its "contract" is the documented behavior `BTC`/`USD` gain when used as a field annotation on a `pydantic.BaseModel` subclass defined by a consumer.

## Field annotation

```python
from pydantic import BaseModel
from monetils import BTC, USD

class Invoice(BaseModel):
    price: USD
    fee: BTC | None = None
```

No wrapper, adapter, or `Annotated[...]` type is required (FR-001).

## Validation contract

| Input to a `BTC`/`USD` field | Outcome |
|---|---|
| An instance of that exact currency class | Accepted as-is, full precision preserved (FR-003). |
| An `int`, `float`, `Decimal`, or numeric `str` | Accepted; interpreted in the currency's base unit, identical to `BTC(value)`/`USD(value)` (FR-002). |
| An instance of the *other* currency class | Rejected: `pydantic.ValidationError`, naming the field (FR-004). |
| An unparseable string, `None` on a required field, or another unsupported type | Rejected: `pydantic.ValidationError`, naming the field (FR-004). |

No `monetils`-specific exception (`MonetilsError`, `CurrencyMismatchError`) ever escapes model construction — all rejections surface as the standard `pydantic.ValidationError`.

## Serialization contract

| Call | Result for a `BTC`/`USD` field |
|---|---|
| `model.model_dump()` | The `BTC`/`USD` instance itself (FR-005). |
| `model.model_dump(mode="json")` | The fixed-decimal string from `str(instance)` (FR-006). |
| `model.model_dump_json()` | Same string, JSON-encoded (FR-006). |

Round-tripping a model through `model_dump_json()` and re-validating reproduces the original value down to the currency's display precision (2 places for `USD`, 8 for `BTC`) — see spec Assumptions for the documented sub-satoshi (millisatoshi) precision trade-off of the JSON path specifically.

## Schema contract

`Invoice.model_json_schema()` succeeds and describes `price`/`fee` as JSON string properties (FR-007) — usable as-is by frameworks that render Pydantic models into OpenAPI docs (e.g. FastAPI), with no custom schema code required from the model author.

## Dependency contract

This feature does **not** add `pydantic` as a `monetils` runtime dependency (FR-009). `import monetils`, and every direct (non-Pydantic) use of `BTC`/`USD`, works with no third-party package installed at all (FR-010). To use `BTC`/`USD` as a Pydantic model field, a consumer must install `pydantic` themselves, as their own project's dependency — `monetils` never installs it for them.

## Backward compatibility

No existing public symbol, signature, or direct (non-Pydantic) behavior changes (FR-008). This is a purely additive capability layered onto the existing `_Currency`/`BTC`/`USD` design from feature 001.
