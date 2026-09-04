"""Exception types for monetils."""


class MonetilsError(Exception):
    """Base class for all monetils-specific errors. Never raised directly."""


class CurrencyMismatchError(MonetilsError):
    """Raised when an operation mixes instances of two different currency classes."""
