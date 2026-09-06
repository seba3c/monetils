---
name: speckit-version-bump
description: Interactively bump the project's version across all sync points after implementation
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: github-spec-kit
  source: version:commands/speckit.version.bump.md
---

# Version Bump

Interactively determine a new project version and synchronize it across all
version sync points after a Spec Kit command completes.

## Behavior

This command is invoked as a hook (currently only `after_implement`). It:

1. Determines the event name from the hook context (e.g., if invoked as an `after_implement` hook, the event is `after_implement`)
2. Checks `.specify/extensions/version/version-config.yml` for the `auto_bump` section
3. Looks up the specific event key to see if version bumping is enabled
4. Falls back to `auto_bump.default` if no event-specific key exists
5. If disabled, or the config file is missing, reports "skipped" and makes no changes
6. If enabled, reads the current version from `pyproject.toml` (`version = "..."` under `[project]`)
7. Determines the new version (see below)
8. If a new version was chosen, runs the script to update all sync points (see Execution below)

## Determining the New Version

1. Read the current version from `pyproject.toml`.
2. Parse the leading `MAJOR.MINOR.PATCH` numeric prefix (ignore any trailing
   pre-release/build suffix, e.g. the `b2` in `0.2.0b2`, when computing
   candidates — but display the full current version string to the user).
3. Compute:
   - PATCH candidate: `MAJOR.MINOR.(PATCH+1)`
   - MINOR candidate: `MAJOR.(MINOR+1).0`
   - MAJOR candidate: `(MAJOR+1).0.0`
4. Ask the user which to use (use the AskUserQuestion tool if available in
   the current agent runtime, otherwise ask as a plain conversational
   multiple-choice question). Offer exactly these options:
   - **PATCH** `<computed value>` — "Backwards-compatible fixes or internal changes only"
   - **MINOR** `<computed value>` — "New backwards-compatible functionality"
   - **MAJOR** `<computed value>` — "Breaking changes to the public API"
   - **No change (skip)** — leave every sync point untouched
   - **Other** — free-text entry for any other version string (e.g. to
     finalize a pre-release like `0.2.0`, or set an arbitrary version)

   Remind the user of the Constitution's semantic versioning policy
   (Principle V in `.specify/memory/constitution.md`): breaking API changes
   require MAJOR; new backward-compatible functionality bumps MINOR;
   fixes/internal changes bump PATCH.
5. If the user chooses "No change (skip)": report that the version was left
   unchanged and stop — do not invoke the script.
6. Otherwise, write the chosen version string to a temporary file using your
   file-editing tool (not a shell `echo`/`printf`), then invoke the script
   with `--version-file <path>` (see Execution below).

## Execution

Determine the event name from the hook that triggered this command, then
(only if the user selected a version to bump to) run the script:

- **Bash**: `.specify/extensions/version/scripts/bash/bump-version.sh <event_name> --version-file <path>`

Replace `<event_name>` with the actual hook event (e.g., `after_implement`).
**Do not interpolate the chosen version directly into a shell command
string** — its content may come from free-text "Other" input and a shell
would happily execute characters like `$(...)` or backticks embedded in it.
Instead, write the version to a temporary file using your file-editing tool,
then pass that file's path via `--version-file <path>`, mirroring the
`--message-file` convention used by `speckit.git.commit`.

## Configuration

In `.specify/extensions/version/version-config.yml`:

```yaml
auto_bump:
  default: false          # Global toggle — set true to enable for all commands
  after_implement:
    enabled: true          # Override per-command

run_uv_lock: true          # Run `uv lock` after bumping, to resync uv.lock
```

## Graceful Degradation

- If no config file exists: the extension still defaults to enabled for `after_implement` (this extension ships enabled-by-default; a missing config should not silently disable its entire purpose)
- If the event is disabled in config: skips with a message, no files touched
- If the user chooses "No change (skip)": skips, no files touched, no script invocation
- If `pyproject.toml` has no `version = "..."` line: fails with a clear error
- If the chosen version does not match a version-like pattern: fails with a clear error before touching any file
- If the chosen version equals the current version: no-ops with a message
- If `uv` is not installed: updates `pyproject.toml` and `src/monetils/__init__.py`, then skips `uv lock` with a warning that `uv.lock` is now stale
- If `uv lock` fails (uv present but resolution/lock error): the version files remain updated (not rolled back); prints a warning telling the user to run `uv lock` manually
