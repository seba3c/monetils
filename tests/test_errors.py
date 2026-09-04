import pytest

from monetils import BTC, USD, CurrencyMismatchError


class TestCrossCurrencyRejection:
    def test_add_raises(self) -> None:
        with pytest.raises(CurrencyMismatchError):
            BTC(1) + USD(1)

    def test_sub_raises(self) -> None:
        with pytest.raises(CurrencyMismatchError):
            BTC(1) - USD(1)

    def test_lt_raises(self) -> None:
        with pytest.raises(CurrencyMismatchError):
            _ = BTC(1) < USD(1)

    def test_gt_raises(self) -> None:
        with pytest.raises(CurrencyMismatchError):
            _ = BTC(1) > USD(1)


class TestUnrecognizedUnit:
    def test_to_unrecognized_unit_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            BTC(1).to("euro")

    def test_construct_with_unrecognized_unit_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            BTC(1, unit="euro")


class TestCrossCurrencyEquality:
    def test_eq_across_currencies_is_false_not_an_error(self) -> None:
        assert BTC(1) != USD(1)

    def test_eq_against_unrelated_type_is_false(self) -> None:
        assert BTC(1) != "1"

    def test_instances_are_hashable(self) -> None:
        assert hash(BTC(1)) == hash(BTC(1))
        assert {BTC(1), BTC(1), BTC(2)} == {BTC(1), BTC(2)}


class TestPrivateBaseAndRegistry:
    def test_instantiating_private_base_directly_raises_type_error(self) -> None:
        from monetils._base import _Currency

        with pytest.raises(TypeError):
            _Currency(1)

    def test_registry_lookup(self) -> None:
        assert BTC.get("USD") is USD
        assert USD.get("BTC") is BTC

    def test_public_export_surface(self) -> None:
        import monetils

        assert set(monetils.__all__) == {
            "BTC",
            "USD",
            "MonetilsError",
            "CurrencyMismatchError",
        }
        assert not hasattr(monetils, "_Currency")
