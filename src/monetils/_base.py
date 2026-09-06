"""Private, currency-agnostic engine shared by all currency classes."""

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import TYPE_CHECKING, ClassVar, Self

from monetils._errors import CurrencyMismatchError

if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
    from pydantic.json_schema import JsonSchemaValue
    from pydantic_core import CoreSchema

_Number = int | float | Decimal


@dataclass(frozen=True)
class Unit:
    """One recognized unit of a currency (e.g. satoshi, cent)."""

    name: str
    symbol: str
    exponent: int
    on_chain: bool = True


class _Currency:
    """Private, non-instantiable base implementing all currency-agnostic behavior.

    Subclasses (`BTC`, `USD`) supply their own `units` table and `base_unit`; every
    other behavior — storage, conversion, formatting, arithmetic, comparison, and the
    currency registry — lives here and is inherited unchanged.
    """

    units: ClassVar[dict[str, Unit]] = {}
    base_unit: ClassVar[str] = ""
    _registry: ClassVar[dict[str, type["_Currency"]]] = {}

    raw: int

    def __new__(cls, *_args: object, **_kwargs: object) -> "_Currency":
        if cls is _Currency:
            msg = "_Currency cannot be instantiated directly; use a subclass such as BTC or USD"
            raise TypeError(msg)
        return super().__new__(cls)

    def __init__(self, value: int | float | Decimal | str, unit: str | None = None) -> None:
        """Construct an amount expressed in `unit` (defaults to the class's base unit)."""
        unit = unit if unit is not None else self.base_unit
        self.raw = self._raw_from_value(value, unit)

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _Currency._registry[cls.base_unit] = cls

    @classmethod
    def _finest_unit(cls) -> Unit:
        return min(cls.units.values(), key=lambda u: u.exponent)

    @classmethod
    def _finest_on_chain_unit(cls) -> Unit:
        on_chain_units = [u for u in cls.units.values() if u.on_chain]
        return min(on_chain_units, key=lambda u: u.exponent)

    @classmethod
    def _raw_from_value(cls, value: int | float | Decimal | str, unit: str) -> int:
        finest = cls._finest_unit()
        unit_def = cls.units[unit]
        exponent_diff = unit_def.exponent - finest.exponent
        amount = Decimal(str(value)) * (Decimal(10) ** exponent_diff)
        return int(amount.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))

    @classmethod
    def from_raw(cls, raw: int) -> Self:
        """Reconstruct an instance directly from its raw finest-unit integer value."""
        instance = cls.__new__(cls)
        instance.raw = raw
        return instance

    @classmethod
    def get(cls, code: str) -> type["_Currency"]:
        """Look up a registered currency class by its base-unit code."""
        return cls._registry[code]

    def to(self, unit: str | None = None) -> Decimal:
        """Convert this amount to `unit` (defaults to the base unit) as an exact `Decimal`."""
        unit = unit if unit is not None else self.base_unit
        finest = self._finest_unit()
        unit_def = self.units[unit]
        exponent_diff = finest.exponent - unit_def.exponent
        return Decimal(self.raw) * (Decimal(10) ** exponent_diff)

    def __str__(self) -> str:
        finest_on_chain = self._finest_on_chain_unit()
        places = -finest_on_chain.exponent
        return f"{self.to(self.base_unit):.{places}f}"

    def __repr__(self) -> str:
        return f"{self} {self.base_unit}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _Currency) or type(other) is not type(self):
            return NotImplemented
        return self.raw == other.raw

    def __hash__(self) -> int:
        return hash((type(self), self.raw))

    def __lt__(self, other: object) -> bool:
        self._require_same_currency(other)
        return self.raw < other.raw

    def __le__(self, other: object) -> bool:
        self._require_same_currency(other)
        return self.raw <= other.raw

    def __gt__(self, other: object) -> bool:
        self._require_same_currency(other)
        return self.raw > other.raw

    def __ge__(self, other: object) -> bool:
        self._require_same_currency(other)
        return self.raw >= other.raw

    def _require_same_currency(self, other: object) -> None:
        if type(other) is not type(self):
            msg = f"Cannot compare {type(self).__name__} with {type(other).__name__}"
            raise CurrencyMismatchError(msg)

    def __add__(self, other: "_Currency | _Number") -> Self:
        return self._combine(other, subtract=False)

    def __sub__(self, other: "_Currency | _Number") -> Self:
        return self._combine(other, subtract=True)

    def _combine(self, other: "_Currency | _Number", *, subtract: bool) -> Self:
        if isinstance(other, _Currency):
            if type(other) is not type(self):
                msg = f"Cannot combine {type(self).__name__} with {type(other).__name__}"
                raise CurrencyMismatchError(msg)
            other_raw = other.raw
        else:
            other_raw = self._raw_from_value(other, self.base_unit)
        new_raw = self.raw - other_raw if subtract else self.raw + other_raw
        return type(self).from_raw(new_raw)

    def __mul__(self, scalar: _Number) -> Self:
        amount = Decimal(self.raw) * Decimal(str(scalar))
        new_raw = int(amount.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
        return type(self).from_raw(new_raw)

    def __truediv__(self, scalar: _Number) -> Self:
        amount = Decimal(self.raw) / Decimal(str(scalar))
        new_raw = int(amount.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
        return type(self).from_raw(new_raw)

    @classmethod
    def _pydantic_validate(cls, value: object) -> Self:
        """Validate a Pydantic field value into an instance of this currency class.

        A same-class instance passes through unchanged (full precision preserved). A
        different currency's instance is rejected before it ever reaches the
        constructor, since `str()` on a `_Currency` instance returns a plain numeric
        string that `Decimal(str(value))` would otherwise silently accept.
        """
        if isinstance(value, cls):
            return value
        if isinstance(value, _Currency):
            msg = f"Expected a {cls.__name__} amount, got a {type(value).__name__} amount"
            raise ValueError(msg)
        try:
            return cls(value)  # type: ignore[arg-type]
        except (TypeError, ValueError, ArithmeticError) as exc:
            msg = f"Cannot interpret {value!r} as a {cls.__name__} amount"
            raise ValueError(msg) from exc

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: object, _handler: "GetCoreSchemaHandler"
    ) -> "CoreSchema":
        """Register this class as a Pydantic v2 custom field type.

        `pydantic_core` is imported here, inside the method body, rather than at
        module scope: this method is only ever called by Pydantic itself, for a
        consumer who is already building a `pydantic.BaseModel` (and therefore
        already has `pydantic`/`pydantic_core` installed as their own dependency).
        Importing it lazily keeps `monetils` itself free of any runtime dependency
        on Pydantic.
        """
        from pydantic_core import core_schema

        return core_schema.no_info_plain_validator_function(
            cls._pydantic_validate,
            serialization=core_schema.plain_serializer_function_ser_schema(str, when_used="json"),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _schema: "CoreSchema", handler: "GetJsonSchemaHandler"
    ) -> "JsonSchemaValue":
        """Describe this class as a plain string in generated JSON Schema."""
        from pydantic_core import core_schema

        json_schema = handler(core_schema.str_schema())
        json_schema["examples"] = [str(cls(1))]
        return json_schema
