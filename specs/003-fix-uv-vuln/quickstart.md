# Quickstart: Uv Dependency Vulnerability Remediation

Validates that the `uv` transitive dependency is patched (GHSA-4gg8-gxpx-9rph / Dependabot alert #1) and that nothing else regressed.

## Prerequisites

- `uv` installed and on `PATH`
- Repository checked out on branch `003-fix-uv-vuln`

## Steps

1. **Check the currently-locked `uv` version**:
   ```bash
   grep -A2 '^name = "uv"' uv.lock
   ```
   Expected before the fix: `version = "0.11.14"` (or any version `< 0.11.15`).

2. **Regenerate the lockfile, upgrading only `uv`**:
   ```bash
   uv lock --upgrade-package uv
   ```

3. **Confirm the resolved version is patched**:
   ```bash
   grep -A2 '^name = "uv"' uv.lock
   ```
   Expected: `version` is `0.11.15` or later (verified: `0.12.10` at the time this was run).

4. **Run the full test suite to confirm no regression**:
   ```bash
   uv run pytest
   ```
   Expected: all tests pass (79 passed at the time this was run), with no new failures.

5. **Confirm only `uv.lock` changed**:
   ```bash
   git status --short
   ```
   Expected: `uv.lock` is the only modified tracked file from this fix (spec/plan/tasks artifacts under `specs/003-fix-uv-vuln/` are separate, expected additions).

## Post-merge validation

After this change is merged to `main`:

- Re-check `https://github.com/seba3c/monetils/security/dependabot/1` — it should move to a resolved/closed state on GitHub's next scan (SC-003).
- Confirm no other Dependabot alerts are open for the repository (SC-004): `gh api repos/seba3c/monetils/dependabot/alerts --jq '[.[] | select(.state=="open")] | length'` should return `0`.
