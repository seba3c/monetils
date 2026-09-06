"""The USD currency class."""

from decimal import Decimal
from typing import ClassVar

from monetils._base import Unit, _Currency


class USD(_Currency):
    """An amount of US dollars.

    Constructed directly in whole USD (`USD(1)` is 1 USD) or via a per-unit classmethod
    (`USD.cent(...)`). Stored internally at cent precision; `str()` formats to 2 decimal
    places.

    Usable directly as a Pydantic v2 model field (e.g. `amount: USD`) with no wrapper
    type required; requires the consumer to have `pydantic` installed themselves.
    """

    base_unit = "USD"
    units: ClassVar[dict[str, Unit]] = {
        "USD": Unit(name="USD", symbol="$", exponent=0),
        "cent": Unit(name="cent", symbol="¢", exponent=-2),
    }

    def __init__(self, value: int | float | Decimal | str, unit: str | None = None) -> None:
        """Construct a USD amount expressed in `unit` (defaults to whole USD)."""
        super().__init__(value, unit)

    @classmethod
    def cent(cls, value: int | float | Decimal | str) -> "USD":
        """Construct a USD amount expressed in cents."""
        return cls(value, unit="cent")

    @property
    def cents(self) -> int:
        """This amount as a whole number of cents."""
        return int(self.to("cent"))
