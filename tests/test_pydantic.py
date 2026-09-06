import json

import pytest
from pydantic import BaseModel, ValidationError

from monetils import BTC, USD, CurrencyMismatchError, MonetilsError


class Invoice(BaseModel):
    price: USD
    fee: BTC


class OptionalFee(BaseModel):
    fee: BTC | None = None


class TestPydanticConstruction:
    def test_construct_from_plain_number(self) -> None:
        inv = Invoice(price=19.99, fee=1)
        assert inv.price == USD(19.99)
        assert inv.fee == BTC(1)

    def test_construct_from_numeric_string(self) -> None:
        inv = Invoice(price="19.99", fee="0.5")
        assert inv.price == USD(19.99)
        assert inv.fee == BTC(0.5)

    def test_construct_from_same_class_instance_preserves_sub_satoshi_precision(self) -> None:
        precise = BTC.msat(100_000_001)  # not a whole satoshi
        inv = Invoice(price=1, fee=precise)
        assert inv.fee is precise
        assert inv.fee.raw == precise.raw

    def test_optional_field_accepts_none(self) -> None:
        model = OptionalFee(fee=None)
        assert model.fee is None

    def test_optional_field_default_is_none(self) -> None:
        assert OptionalFee().fee is None

    def test_sibling_fields_of_different_currencies_validate_independently(self) -> None:
        inv = Invoice(price=USD(5), fee=BTC(1))
        assert inv.price == USD(5)
        assert inv.fee == BTC(1)


class TestPydanticJsonSchema:
    def test_schema_generation_succeeds_with_string_types(self) -> None:
        schema = Invoice.model_json_schema()
        assert schema["properties"]["price"]["type"] == "string"
        assert schema["properties"]["fee"]["type"] == "string"


class TestPydanticSerialization:
    def test_model_dump_python_mode_returns_instance(self) -> None:
        inv = Invoice(price=19.99, fee=1)
        dumped = inv.model_dump()
        assert dumped["price"] is inv.price
        assert dumped["fee"] is inv.fee

    def test_model_dump_json_mode_uses_str_convention(self) -> None:
        inv = Invoice(price=19.99, fee=1)
        dumped = inv.model_dump(mode="json")
        assert dumped == {"price": "19.99", "fee": "1.00000000"}

    def test_model_dump_json_string(self) -> None:
        inv = Invoice(price=19.99, fee=1)
        payload = json.loads(inv.model_dump_json())
        assert payload == {"price": "19.99", "fee": "1.00000000"}

    def test_round_trip_via_json_reproduces_original(self) -> None:
        inv = Invoice(price=19.99, fee=1)
        restored = Invoice.model_validate_json(inv.model_dump_json())
        assert restored == inv

    def test_json_round_trip_rounds_sub_satoshi_remainder(self) -> None:
        precise = BTC.msat(100_000_001)  # 100_000 sat + 1 msat remainder
        model = OptionalFee(fee=precise)
        restored = OptionalFee.model_validate_json(model.model_dump_json())
        assert restored.fee == BTC.sat(100_000)
        assert restored.fee != precise


class TestPydanticValidationErrors:
    def test_wrong_currency_instance_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Invoice(price=1, fee=USD(1))
        assert exc_info.value.errors()[0]["loc"] == ("fee",)

    def test_wrong_currency_instance_reverse_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Invoice(price=BTC(1), fee=1)
        assert exc_info.value.errors()[0]["loc"] == ("price",)

    def test_unparseable_string_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Invoice(price="not-a-number", fee=1)
        assert exc_info.value.errors()[0]["loc"] == ("price",)

    def test_none_on_required_field_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Invoice(price=None, fee=1)
        assert exc_info.value.errors()[0]["loc"] == ("price",)

    def test_no_monetils_exception_escapes_model_construction(self) -> None:
        for bad_value in (USD(1), "nonsense", None, [1, 2]):
            try:
                Invoice(price=bad_value, fee=1)
            except ValidationError:
                continue
            except (MonetilsError, CurrencyMismatchError):
                pytest.fail("a monetils-internal exception escaped model construction")
