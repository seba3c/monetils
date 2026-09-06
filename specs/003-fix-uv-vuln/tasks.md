---

description: "Task list template for feature implementation"
---

# Tasks: Uv Dependency Vulnerability Remediation

**Input**: Design documents from `/specs/003-fix-uv-vuln/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md (N/A — no entities), quickstart.md

**Tests**: Not requested for this feature — the existing test suite is re-run unmodified as the regression check (no new test code is written).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths / commands in descriptions

## Path Conventions

Single project (existing `monetils` library layout): repository root for `pyproject.toml` / `uv.lock`, `tests/` for the test suite. No new files or directories are created by this feature.

---

## Phase 1: Setup

**Purpose**: Confirm the environment this fix will be applied and verified in

- [X] T001 Confirm `uv` is installed and the working tree is on branch `003-fix-uv-vuln` (repo root)

---

## Phase 2: Foundational

No foundational tasks — this fix touches a single existing file (`uv.lock`) and has no shared infrastructure, schema, or scaffolding prerequisites for the user stories below.

---

## Phase 3: User Story 1 - Eliminate the vulnerable uv version from the lockfile (Priority: P1) 🎯 MVP

**Goal**: `uv.lock` resolves `uv` to `0.11.15` or later, and the existing test suite still passes.

**Independent Test**: Inspect `uv.lock` and confirm the `uv` package entry resolves to `0.11.15`+; re-run `uv run pytest` and confirm all tests pass.

- [X] T002 [US1] Inspect the currently-pinned `uv` version in `uv.lock` (repo root) to confirm it is below `0.11.15` (`grep -A2 '^name = "uv"' uv.lock`)
- [X] T003 [US1] Regenerate the lockfile, upgrading only the `uv` package: `uv lock --upgrade-package uv` (repo root, modifies `uv.lock`)
- [X] T004 [US1] Verify `uv.lock`'s `uv` entry now resolves to `0.11.15` or later (repo root, `uv.lock`)
- [X] T005 [US1] Run the full test suite to confirm no regression: `uv run pytest` (repo root) — expect all existing tests to pass unmodified

**Checkpoint**: At this point, User Story 1 is fully implemented and independently verifiable — the vulnerable `uv` version is gone from `uv.lock` and the test suite is green.

---

## Phase 4: User Story 2 - Confirm no other dependencies are affected (Priority: P2)

**Goal**: Verify Dependabot alert #1 was the only open alert, and that it closes after this fix merges.

**Independent Test**: Query the repository's Dependabot alerts before and after merge.

- [X] T006 [P] [US2] Query open Dependabot alerts and confirm alert #1 (GHSA-4gg8-gxpx-9rph) is the only one open: `gh api repos/seba3c/monetils/dependabot/alerts --jq '[.[] | select(.state=="open")]'` — confirmed: alert #1 is the only open alert
- [ ] T007 [US2] After this branch is merged to `main`, re-query Dependabot alerts and confirm zero remain open (validates spec Success Criteria SC-003 and SC-004): `gh api repos/seba3c/monetils/dependabot/alerts --jq '[.[] | select(.state=="open")] | length'` — **pending**: not yet mergeable to `main` from this session; run after merge

**Checkpoint**: T006 can run any time (read-only, no dependency on T002-T005). T007 is a post-merge validation step and must run after this branch's changes reach `main`.

---

## Dependencies & Execution Order

- **Phase 1 (Setup)** has no dependencies — start here.
- **Phase 2 (Foundational)**: none — proceed directly to Phase 3.
- **User Story 1 (Phase 3)**: T002 → T003 → T004 → T005, strictly sequential (each step depends on the previous file state). Depends only on Phase 1.
- **User Story 2 (Phase 4)**: T006 has no dependency on US1 and can run in parallel with Phase 3 at any point. T007 depends on this branch being merged to `main` (i.e., after Phase 3 completes and the PR merges), not on T006.
- No Polish/cross-cutting phase is needed — this fix changes no public behavior, so no README/docstring updates are required per the project constitution.

## Parallel Execution Example

```bash
# T006 (Dependabot alert check) can run in parallel with the US1 fix (T002-T005),
# since it only reads GitHub state and touches no local files:
gh api repos/seba3c/monetils/dependabot/alerts --jq '[.[] | select(.state=="open")]' &
uv lock --upgrade-package uv
wait
```

## Implementation Strategy

**MVP = User Story 1 (T001-T005)**: this alone fully resolves the vulnerability and is independently mergeable/deployable. User Story 2 (T006-T007) is verification/bookkeeping that confirms the fix is complete and no other alerts were missed — valuable but not blocking for the fix itself.

1. Complete Phase 1 (T001).
2. Complete Phase 3 / US1 (T002-T005) — this is the deliverable.
3. Run T006 any time before merge (parallelizable, read-only).
4. Merge, then run T007 to confirm closure.
