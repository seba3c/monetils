# Research: Uv Dependency Vulnerability Remediation

No `[NEEDS CLARIFICATION]` markers were left in the spec or Technical Context, so this phase documents the one real decision (how to apply the fix) rather than resolving open unknowns.

## Decision: Regenerate `uv.lock` via `uv lock --upgrade-package uv`

**Rationale**: `uv` is not a direct dependency anywhere in `pyproject.toml` — it is pulled in transitively by `tox-uv` (declared in `[dependency-groups].dev` and the `test` extra). There is nowhere to add an explicit `uv>=0.11.15` constraint even if desired, since `monetils` itself never lists `uv` as a dependency. `uv lock --upgrade-package uv` asks the resolver to re-solve specifically that package to the newest version compatible with the rest of the graph, which is the narrowest possible change (verified in a prior session: it moved `uv` from `0.11.14` to `0.12.10` and touched no other package in `uv.lock`).

**Alternatives considered**:
- **Hand-editing the `version = "0.11.14"` line in `uv.lock` for the `uv` entry**: rejected — `uv.lock` is a generated file with hashes and a full dependency graph; hand-editing a version string without updating the corresponding `sdist`/`wheel` URLs and hashes would produce a lockfile that fails integrity checks on the next `uv sync`.
- **A full unconstrained `uv lock --upgrade`**: rejected in favor of the narrower `--upgrade-package uv` — upgrading every dependency at once is a larger, unrelated blast radius for what is specifically a single-package security fix; a targeted upgrade is easier to review and revert if needed.
- **Adding an explicit `uv>=0.11.15` marker somewhere in `pyproject.toml`**: rejected — there is no dependency-groups entry for `uv` to constrain (only `tox-uv` is listed), and adding a phantom direct dependency on a tool that's actually resolved transitively would misrepresent the dependency graph without changing how it resolves.

## Decision: Verify via the existing test suite, not new tests

**Rationale**: This change has zero code-path surface — `uv` is dev/CI tooling, never imported by `src/monetils` or exercised by any test. The correct verification is (a) confirming the resolved version in `uv.lock`, and (b) confirming the *existing* test suite still passes unmodified, proving the newer `uv` didn't break the dev/test toolchain itself.

**Alternatives considered**:
- **Writing a new test asserting the `uv` version**: rejected — `uv` version is a dev-environment fact, not project behavior; asserting it in `tests/` would conflate tooling pinning with the library's own test suite and constitution Principle II ("New behavior MUST be covered by tests") doesn't apply since no new behavior is introduced.
