"""The BTC currency class."""

from decimal import Decimal
from typing import ClassVar

from monetils._base import Unit, _Currency


class BTC(_Currency):
    """An amount of bitcoin.

    Constructed directly in whole BTC (`BTC(1)` is 1 BTC) or via a per-unit classmethod
    (`BTC.mBTC(...)`, `BTC.sat(...)`, `BTC.msat(...)`). Stored internally at millisatoshi
    precision (its finest recognized unit); `str()` formats to 8 decimal places (satoshi,
    its finest unit that settles on-chain).

    Usable directly as a Pydantic v2 model field (e.g. `amount: BTC`) with no wrapper
    type required; requires the consumer to have `pydantic` installed themselves.
    """

    base_unit = "BTC"
    units: ClassVar[dict[str, Unit]] = {
        "BTC": Unit(name="BTC", symbol="BTC", exponent=0),
        "mBTC": Unit(name="mBTC", symbol="mBTC", exponent=-3),
        "sat": Unit(name="sat", symbol="sat", exponent=-8),
        "msat": Unit(name="msat", symbol="msat", exponent=-11, on_chain=False),
    }

    def __init__(self, value: int | float | Decimal | str, unit: str | None = None) -> None:
        """Construct a BTC amount expressed in `unit` (defaults to whole BTC)."""
        super().__init__(value, unit)

    @classmethod
    def mBTC(cls, value: int | float | Decimal | str) -> "BTC":  # noqa: N802
        """Construct a BTC amount expressed in millibitcoin."""
        return cls(value, unit="mBTC")

    @classmethod
    def sat(cls, value: int | float | Decimal | str) -> "BTC":
        """Construct a BTC amount expressed in satoshis."""
        return cls(value, unit="sat")

    @classmethod
    def msat(cls, value: int | float | Decimal | str) -> "BTC":
        """Construct a BTC amount expressed in millisatoshis."""
        return cls(value, unit="msat")

    @property
    def sats(self) -> int:
        """This amount as a whole number of satoshis."""
        return int(self.to("sat"))
