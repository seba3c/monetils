import pytest

from monetils import USD


class TestUSDConstruction:
    def test_str_typical_amount(self) -> None:
        assert str(USD(1234.5)) == "1234.50"

    def test_str_negative(self) -> None:
        assert str(USD(-5)) == "-5.00"

    def test_str_zero(self) -> None:
        assert str(USD(0)) == "0.00"

    def test_repr(self) -> None:
        assert repr(USD(1234.5)) == "1234.50 USD"


class TestUSDArithmetic:
    def test_add_same_class(self) -> None:
        assert USD(10.50) + USD(5.25) == USD(15.75)

    def test_sub_same_class(self) -> None:
        assert USD(15.75) - USD(5.25) == USD(10.50)

    def test_add_plain_number_as_amount(self) -> None:
        assert USD(1) + 1 == USD(2)

    def test_sub_plain_number_as_amount(self) -> None:
        assert USD(2) - 1 == USD(1)

    def test_mul_plain_number_as_scaling_factor(self) -> None:
        assert USD(1) * 2 == USD(2)

    def test_div_plain_number_as_scaling_factor(self) -> None:
        assert USD(2) / 2 == USD(1)

    def test_div_rounds_to_nearest_raw_unit(self) -> None:
        # 10 cents / 3 = 3.333... -> rounds to nearest whole cent (3, HALF_EVEN)
        assert (USD.from_raw(10) / 3).raw == 3

    def test_div_by_zero_raises_zero_division_error(self) -> None:
        with pytest.raises(ZeroDivisionError):
            USD(1) / 0


class TestUSDComparison:
    def test_eq(self) -> None:
        assert USD(1) == USD(1)
        assert USD(1) != USD(2)

    def test_lt(self) -> None:
        assert USD(1) < USD(2)

    def test_le(self) -> None:
        assert USD(1) <= USD(1)
        assert USD(1) <= USD(2)

    def test_gt(self) -> None:
        assert USD(2) > USD(1)

    def test_ge(self) -> None:
        assert USD(1) >= USD(1)
        assert USD(2) >= USD(1)


class TestUSDUnitConversion:
    def test_to_cent(self) -> None:
        assert USD(19.99).to("cent") == 1999

    def test_cents_property(self) -> None:
        assert USD(19.99).cents == 1999

    def test_cent_classmethod(self) -> None:
        assert USD.cent(1999) == USD(19.99)
        assert str(USD.cent(1999)) == "19.99"

    def test_round_trip_via_from_raw(self) -> None:
        original = USD(19.99)
        reconstructed = USD.from_raw(original.raw)
        assert reconstructed == original

    def test_excess_precision_rounds_at_cent_boundary(self) -> None:
        # 1.005 rounds to the nearest whole cent via ROUND_HALF_EVEN -> 100 (1.00)
        assert USD(1.005).raw == 100
