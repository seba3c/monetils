# Feature Specification: Uv Dependency Vulnerability Remediation

**Feature Branch**: `003-fix-uv-vuln`

**Created**: 2026-09-06

**Status**: Draft

**Input**: User description: "https://github.com/seba3c/monetils/security/dependabot/1"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Eliminate the vulnerable uv version from the lockfile (Priority: P1)

As a project maintainer, I want the version of `uv` resolved in the project's dependency lockfile to be a patched release, so that anyone who runs `uv sync`/`uv lock` to set up the project does not pull in a version of `uv` with a known arbitrary-file-write vulnerability (GHSA-4gg8-gxpx-9rph).

**Why this priority**: This is the entire scope of the fix. `uv` is a transitive development-only dependency (pulled in via `tox-uv`), not a runtime dependency shipped to consumers of the `monetils` library — but it is still resolved and executed locally and in CI whenever the dev environment is set up, so leaving the vulnerable version pinned exposes maintainers and CI to the wheel-installation risk described in the advisory.

**Independent Test**: Inspect `uv.lock` and confirm the `uv` package entry resolves to version `0.11.15` or later; re-run the project's full test suite to confirm nothing regresses from the dependency bump.

**Acceptance Scenarios**:

1. **Given** `uv.lock` currently pins `uv` to a version older than `0.11.15`, **When** the lockfile is regenerated, **Then** `uv.lock` resolves `uv` to `0.11.15` or later.
2. **Given** the updated lockfile, **When** the project's test suite is run via `uv run pytest`, **Then** all tests pass with no regressions attributable to the dependency change.
3. **Given** the updated lockfile is merged to the default branch, **When** GitHub Dependabot next re-scans the repository, **Then** Dependabot alert #1 (GHSA-4gg8-gxpx-9rph) is automatically closed as resolved.

---

### User Story 2 - Confirm no other dependencies are affected (Priority: P2)

As a project maintainer, I want confirmation that no other currently-open Dependabot alerts exist for this repository, so that I know this fix fully closes out the repository's known-vulnerability backlog rather than leaving other alerts unaddressed.

**Why this priority**: Lower priority than the fix itself, but validating the full alert list prevents a false sense of completion — the fix should either close every open alert, or any remaining alerts should be explicitly acknowledged as out of scope.

**Independent Test**: Query the repository's Dependabot alerts and confirm alert #1 is the only entry before the fix, and that its state changes from open to resolved once the fix lands.

**Acceptance Scenarios**:

1. **Given** the repository's Dependabot alerts are listed, **When** alert #1 is the only open alert before the fix, **Then** after the fix is merged no open alerts remain.

---

### Edge Cases

- What happens if a newer `uv` release reintroduces a regression or breaks the pinned Python toolchain? The lockfile update must be validated against the existing test suite (User Story 1, Acceptance Scenario 2) before merging.
- What happens if `uv` is pulled in transitively by a different package in the future (e.g., a `tox-uv` version bump changes its own dependency graph)? Any future alert on `uv` (or any other transitive dependency) follows the same remediation path: regenerate the lockfile and re-verify tests.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project's lockfile (`uv.lock`) MUST resolve the `uv` package to version `0.11.15` or later (the first version containing the fix for GHSA-4gg8-gxpx-9rph).
- **FR-002**: The dependency update MUST NOT change any runtime dependency of the published `monetils` package (`uv` is dev-tooling only, pulled in transitively via the `tox-uv` dev dependency).
- **FR-003**: The full test suite MUST pass after the lockfile update, with no test changes required to accommodate the new `uv` version.
- **FR-004**: The fix MUST result in Dependabot alert #1 for this repository being resolved (closed) once merged to the default branch.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `uv.lock` pins `uv` to a version of `0.11.15` or later (verified by inspection).
- **SC-002**: 100% of the existing test suite passes after the change, with zero new failures.
- **SC-003**: GitHub Dependabot alert #1 (`https://github.com/seba3c/monetils/security/dependabot/1`) is in a resolved/closed state within one scan cycle after the fix is merged to the default branch.
- **SC-004**: Zero open Dependabot alerts remain for the repository after the fix is merged.

## Assumptions

- The vulnerable `uv` version is only ever used as local/CI dev tooling (via the `tox-uv`/`dev` dependency group) and is never a runtime dependency of code shipped to `monetils` consumers, so no changes to `pyproject.toml`'s runtime `dependencies` list are required — only lockfile resolution is affected.
- Regenerating the lockfile (`uv lock`, optionally `--upgrade-package uv`) is sufficient to pick up the patched version, since no explicit upper-bound version constraint on `uv` exists anywhere in the dependency graph that would prevent resolving to `0.11.15` or later.
- Closing the Dependabot alert itself is handled automatically by GitHub once it re-scans the merged lockfile; no manual dismissal step is in scope.
