# Research: BTC and USD Money Representations

**Feature**: 001-btc-usd-money-types | **Date**: 2026-09-04 (regenerated after spec redesign)

No `[NEEDS CLARIFICATION]` markers remain in the spec — the Clarifications session pinned down the class hierarchy, storage precision, display precision, error types, and public surface in detail (including two rounds of user-supplied reference code). This document records the implementation-level decisions needed to turn that design into code that also satisfies the project constitution.

## Decision: implement per-unit classmethods as explicit, hand-written methods — not via `__init_subclass__` + dynamic `setattr`

**Rationale**: The user's reference implementation auto-generates `BTC.sat(...)`, `BTC.mBTC(...)`, `BTC.msat(...)`, `USD.cent(...)` dynamically in `__init_subclass__` via `setattr(cls, name, classmethod(...))`. That's elegant at runtime, but Constitution Principle III (Typed Public API) requires the public API to carry complete type hints — attributes injected via `setattr` at class-creation time are invisible to static type checkers (mypy/pyright) with no extra work, and `monetils` ships `py.typed` specifically so consumers get static checking. Explicitly defining `sat`, `mBTC`, `msat` on `BTC` (and `cent` on `USD`) as ordinary typed classmethods — each a one-line delegation to a shared private helper on `_Currency` — keeps the exact same runtime behavior and the "don't repeat the conversion logic per currency" property, while remaining fully visible and typed for static analysis. This is an adaptation of the reference code's *mechanism*, not a change to its *behavior* — `BTC.sat(50_000_000)` still returns a `BTC` instance identically.

**Alternatives considered**:
- Dynamic `setattr` exactly as shown in the reference code — rejected: invisible to static type checkers, conflicts with Constitution Principle III.
- Dynamic `setattr` plus a hand-written `.pyi` stub file duplicating the signatures — rejected: adds a second place every new unit must be kept in sync, more error-prone than just writing the classmethod.

## Decision: `raw` storage precision is each currency's finest *recognized* unit (not its finest *on-chain* unit)

**Rationale**: The spec (FR-006) fixes this explicitly: BTC stores at millisatoshi precision (even though millisatoshi never settles on-chain — it's a Lightning-only accounting unit), USD at cent precision. This is a deliberate supersession of this feature's very first draft, which had fixed satoshi as BTC's boundary; the user's reference code computes `raw`'s scale from *all* defined units (`min(units.values(), key=exponent)`), not just the on-chain ones. Display precision (FR-009) is a separate, coarser calculation that *does* filter to on-chain units only — that's why `str(BTC(1))` shows 8 places (satoshi) while `raw` itself carries 11 places (millisatoshi) of precision.

**Alternatives considered**: satoshi as the single precision boundary for both storage and display (this feature's earlier design) — superseded once the reference code and the user's explicit confirmation fixed millisatoshi as the storage boundary.

## Decision: unit ratios are computed as powers of ten (`Decimal(10) ** exponent_diff`), not `fractions.Fraction`

**Rationale**: Every unit in both `BTC` and `USD` is defined by a base-10 exponent relative to the currency's base unit (mBTC = 10⁻³, satoshi = 10⁻⁸, millisatoshi = 10⁻¹¹, cent = 10⁻²). Because all ratios are clean powers of ten, `decimal.Decimal` alone gives exact conversion arithmetic with no need for arbitrary-denominator rational numbers. This simplifies (and supersedes) this feature's earlier `fractions.Fraction`-based decision, which anticipated non-power-of-ten ratios that never actually appear in this design.

**Alternatives considered**: `fractions.Fraction` (this feature's earlier decision) — no longer needed once every unit turned out to be a power-of-ten multiple; `float` — rejected throughout for the usual binary-rounding-error reason.

## Decision: rounding at the precision boundary uses `Decimal.quantize(..., rounding=ROUND_HALF_EVEN)`, not `int()` truncation

**Rationale**: FR-006 requires "round to the nearest" whole unit at the precision boundary — this was an explicit, deliberate choice made during clarification (truncation was offered as an alternative and rejected). The user's reference code's `int(Decimal(str(value)) * factor)` truncates toward zero, which does not satisfy FR-006 as written; it's read here as an illustrative simplification in the sketch, not a deliberate re-opening of the truncation-vs-rounding question (no test in the reference code exercises a case where the two would differ). `ROUND_HALF_EVEN` (banker's rounding) is the same tie-break convention decided in this feature's very first research pass and remains the standard default for financial rounding.

**Alternatives considered**: `int()` truncation (matches the literal reference code, but contradicts FR-006); `ROUND_HALF_UP` (simpler but statistically biased, and not what FR-006's clarification settled on).

## Decision: the private base class blocks direct instantiation via a `__new__` check, not `abc.ABC`

**Rationale**: The reference code's pattern — `if cls is Currency: raise TypeError(...)` inside `__new__` — gives full control over the error message and doesn't require inventing an `@abstractmethod` that has no natural reason to exist (there's no method `_Currency` fails to implement; it's a "don't construct the base directly" marker, not a template-method abstract class). Matches FR-002 exactly: plain built-in `TypeError`.

**Alternatives considered**: `abc.ABC` + `@abstractmethod` — rejected; would need a contrived abstract method with no behavioral purpose, and produces Python's generic abstract-class message rather than the clearer domain-specific one.

## Decision: `Currency.get(code)`'s return type is written as `type[BTC] | type[USD]`, not `type[_Currency]`

**Rationale**: `_Currency` is private and must never appear in a public method's type signature — a consumer reading `BTC.get(...)`'s return type shouldn't see a name they can't import. Since only `BTC` and `USD` are registered today, the explicit union is both accurate and keeps the private base out of the public typing surface. This needs revisiting (documented as a known follow-up, not a spec gap) if/when a third currency is added — FR-016's registry mechanism itself doesn't need code changes, but this one return-type annotation will need the new class added to the union.

**Alternatives considered**: `type[_Currency]` — rejected, leaks a private name into a public signature; `type[Any]` — rejected, throws away real type information for no benefit.

## Decision: instances are conventionally immutable but not enforced via `__slots__`/frozen dataclass

**Rationale**: Neither reference implementation enforces immutability (`raw` is a plain settable attribute, and `from_raw` builds an instance via `cls.__new__(cls)` before setting it) — matching that behavior exactly avoids inventing a constraint the user didn't ask for. `BTC`/`USD` are documented as value types that should not be mutated after construction, but this is a convention, not a runtime guarantee, consistent with the reference code.

**Alternatives considered**: `@dataclass(frozen=True)` for `_Currency`/`BTC`/`USD` — rejected as unrequested extra behavior; can be added later without breaking the public contract if desired (frozen is stricter, so it's a backward-compatible tightening, not a breaking change).

## Decision: testing and tooling — no change from this feature's first research pass

`pytest` + `pytest-cov` (`fail_under = 90`, already configured), run via `uv run pytest`; `tox` across Python 3.11/3.12/3.13. No new dev dependency is needed for anything in this design (`decimal`, `dataclasses` are stdlib).
