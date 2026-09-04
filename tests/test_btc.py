from decimal import Decimal

import pytest

from monetils import BTC


class TestBTCConstruction:
    def test_str_one_btc(self) -> None:
        assert str(BTC(1)) == "1.00000000"

    def test_str_half_btc(self) -> None:
        assert str(BTC(0.5)) == "0.50000000"

    def test_str_negative(self) -> None:
        assert str(BTC(-1)) == "-1.00000000"

    def test_str_zero(self) -> None:
        assert str(BTC(0)) == "0.00000000"

    def test_repr(self) -> None:
        assert repr(BTC(1)) == "1.00000000 BTC"


class TestBTCArithmetic:
    def test_add_same_class(self) -> None:
        assert BTC(1) + BTC(1) == BTC(2)

    def test_sub_same_class(self) -> None:
        assert BTC(2) - BTC(1) == BTC(1)

    def test_add_plain_number_as_amount(self) -> None:
        assert BTC(1) + 1 == BTC(2)

    def test_sub_plain_number_as_amount(self) -> None:
        assert BTC(2) - 1 == BTC(1)

    def test_mul_plain_number_as_scaling_factor(self) -> None:
        assert BTC(1) * 2 == BTC(2)

    def test_div_plain_number_as_scaling_factor(self) -> None:
        assert BTC(2) / 2 == BTC(1)

    def test_div_rounds_to_nearest_raw_unit(self) -> None:
        # 10 msat / 3 = 3.333... -> rounds to nearest whole msat (4, HALF_EVEN)
        assert (BTC.from_raw(10) / 3).raw == 3

    def test_div_by_zero_raises_zero_division_error(self) -> None:
        with pytest.raises(ZeroDivisionError):
            BTC(1) / 0


class TestBTCComparison:
    def test_eq(self) -> None:
        assert BTC(1) == BTC(1)
        assert BTC(1) != BTC(2)

    def test_lt(self) -> None:
        assert BTC(1) < BTC(2)

    def test_le(self) -> None:
        assert BTC(1) <= BTC(1)
        assert BTC(1) <= BTC(2)

    def test_gt(self) -> None:
        assert BTC(2) > BTC(1)

    def test_ge(self) -> None:
        assert BTC(1) >= BTC(1)
        assert BTC(2) >= BTC(1)


class TestBTCUnitConversion:
    def test_to_sat(self) -> None:
        assert BTC(1).to("sat") == 100_000_000

    def test_to_mbtc(self) -> None:
        assert BTC(1).to("mBTC") == 1000

    def test_to_msat(self) -> None:
        assert BTC(1).to("msat") == 100_000_000_000

    def test_sats_property(self) -> None:
        assert BTC(1).sats == 100_000_000

    def test_mbtc_classmethod(self) -> None:
        assert BTC.mBTC(1000) == BTC(1)

    def test_sat_classmethod(self) -> None:
        assert BTC.sat(50_000_000) == BTC(0.5)

    def test_msat_classmethod(self) -> None:
        assert BTC.msat(100_000_000_000) == BTC(1)

    def test_round_trip_via_msat(self) -> None:
        original = BTC(1)
        msat_value = original.to("msat")
        reconstructed = BTC.msat(msat_value)
        assert reconstructed == original
        assert BTC.from_raw(reconstructed.raw) == original

    def test_excess_precision_rounds_at_msat_boundary(self) -> None:
        # 1 msat is 1e-11 BTC; half of that (5e-12 BTC) rounds to the nearest whole msat.
        assert BTC(Decimal("0.000000000015")).raw == 2
