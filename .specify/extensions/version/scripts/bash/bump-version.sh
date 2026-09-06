#!/usr/bin/env bash
# Version extension: bump-version.sh
# Interactively-chosen version bump, applied across all version sync points
# (pyproject.toml, src/monetils/__init__.py, uv.lock).
#
# Usage: bump-version.sh <event_name> --version-file <path>
#   e.g.: bump-version.sh after_implement --version-file /tmp/speckit-version.txt
#
# --version-file is the only supported way to supply the new version: it
# reads the version from a file instead of a shell argument, so a value that
# may have come from free-text agent/user input is never interpolated into a
# shell command line.

set -e

EVENT_NAME="${1:-}"
if [ -z "$EVENT_NAME" ]; then
    echo "Usage: $0 <event_name> --version-file <path>" >&2
    exit 1
fi
shift || true

VERSION_FILE=""
while [ $# -gt 0 ]; do
    case "$1" in
        --version-file)
            VERSION_FILE="${2:-}"
            if [ -z "$VERSION_FILE" ]; then
                echo "[specify] Error: --version-file requires a path argument" >&2
                exit 1
            fi
            if [ ! -f "$VERSION_FILE" ]; then
                echo "[specify] Error: version file '$VERSION_FILE' not found" >&2
                exit 1
            fi
            shift 2
            ;;
        *)
            echo "[specify] Error: unrecognized argument '$1'" >&2
            exit 1
            ;;
    esac
done

if [ -z "$VERSION_FILE" ]; then
    echo "[specify] No version file supplied; nothing to bump" >&2
    exit 0
fi

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

_find_project_root() {
    local dir="$1"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.specify" ] || [ -d "$dir/.git" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

REPO_ROOT=$(_find_project_root "$SCRIPT_DIR") || REPO_ROOT="$(pwd)"
cd "$REPO_ROOT"

# The version file is a transport-only artifact: its content is captured
# here, so remove it immediately. Otherwise, if it was written inside the
# worktree, it would be picked up as an untracked change by `git status`
# and pollute a later auto-commit hook even when nothing else changed.
NEW_VERSION="$(cat "$VERSION_FILE" | tr -d '[:space:]')"
rm -f "$VERSION_FILE"

# Read per-command config from version-config.yml
_config_file="$REPO_ROOT/.specify/extensions/version/version-config.yml"
_enabled=true
_run_uv_lock=true

if [ -f "$_config_file" ]; then
    _enabled=false
    _in_auto_bump=false
    _in_event=false
    _default_enabled=false

    while IFS= read -r _line; do
        if echo "$_line" | grep -q '^auto_bump:'; then
            _in_auto_bump=true
            _in_event=false
            continue
        fi

        # Exit auto_bump section on next top-level key
        if $_in_auto_bump && echo "$_line" | grep -Eq '^[a-z]'; then
            _in_auto_bump=false
            _in_event=false
        fi

        if $_in_auto_bump; then
            if echo "$_line" | grep -Eq "^[[:space:]]+default:[[:space:]]"; then
                _val=$(echo "$_line" | sed 's/^[^:]*:[[:space:]]*//' | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
                [ "$_val" = "true" ] && _default_enabled=true
            fi

            if echo "$_line" | grep -Eq "^[[:space:]]+${EVENT_NAME}:"; then
                _in_event=true
                continue
            fi

            if $_in_event; then
                if echo "$_line" | grep -Eq '^[[:space:]]{2}[a-z]' && ! echo "$_line" | grep -Eq '^[[:space:]]{4}'; then
                    _in_event=false
                    continue
                fi
                if echo "$_line" | grep -Eq '[[:space:]]+enabled:'; then
                    _val=$(echo "$_line" | sed 's/^[^:]*:[[:space:]]*//' | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
                    [ "$_val" = "true" ] && _enabled=true
                    [ "$_val" = "false" ] && _enabled=false
                fi
            fi
        fi

        if echo "$_line" | grep -Eq '^run_uv_lock:'; then
            _val=$(echo "$_line" | sed 's/^[^:]*:[[:space:]]*//' | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
            [ "$_val" = "false" ] && _run_uv_lock=false
            [ "$_val" = "true" ] && _run_uv_lock=true
        fi
    done < "$_config_file"

    # If event-specific key not found, use default
    if [ "$_enabled" = "false" ] && [ "$_default_enabled" = "true" ]; then
        if ! grep -q "^[[:space:]]*${EVENT_NAME}:" "$_config_file" 2>/dev/null; then
            _enabled=true
        fi
    fi
else
    # No config file — this extension ships enabled-by-default for
    # after_implement, so a missing config should not silently disable it
    # (unlike the git extension's auto-commit, which is opt-in).
    _enabled=true
fi

if [ "$_enabled" != "true" ]; then
    echo "[specify] Version bump disabled for $EVENT_NAME (auto_bump); skipped" >&2
    exit 0
fi

# Skip sentinels
_new_version_lower=$(echo "$NEW_VERSION" | tr '[:upper:]' '[:lower:]')
if [ -z "$NEW_VERSION" ] || [ "$_new_version_lower" = "skip" ] || [ "$_new_version_lower" = "none" ]; then
    echo "[specify] No version change requested; skipped" >&2
    exit 0
fi

# Validate format: numeric X.Y.Z, optionally followed by a pre-release/build
# suffix with no leading dot/space (covers strict semver and PEP 440-ish
# strings like the current "0.2.0b2").
if ! echo "$NEW_VERSION" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+([A-Za-z0-9][A-Za-z0-9.+-]*)?$'; then
    echo "[specify] Error: '$NEW_VERSION' is not a valid version string" >&2
    exit 1
fi

CURRENT_VERSION=$(grep -m1 -E '^version[[:space:]]*=[[:space:]]*"' pyproject.toml 2>/dev/null | sed -E 's/^version[[:space:]]*=[[:space:]]*"([^"]*)".*/\1/')
if [ -z "$CURRENT_VERSION" ]; then
    echo "[specify] Error: could not find a 'version = \"...\"' line in pyproject.toml" >&2
    exit 1
fi

if [ "$NEW_VERSION" = "$CURRENT_VERSION" ]; then
    echo "[specify] Version unchanged ($CURRENT_VERSION); nothing to do" >&2
    exit 0
fi

# Rewrite pyproject.toml's version line (awk + mv rather than sed -i, for
# portability across BSD sed on macOS and GNU sed on Linux).
awk -v new="$NEW_VERSION" '
    !done && $0 ~ /^version[[:space:]]*=[[:space:]]*"/ {
        sub(/"[^"]*"/, "\"" new "\"")
        done = 1
    }
    { print }
' pyproject.toml > pyproject.toml.tmp && mv pyproject.toml.tmp pyproject.toml

if ! grep -q -E "^version[[:space:]]*=[[:space:]]*\"$NEW_VERSION\"" pyproject.toml; then
    echo "[specify] Error: failed to update version in pyproject.toml" >&2
    exit 1
fi

# Rewrite src/monetils/__init__.py's __version__ line
_init_file="src/monetils/__init__.py"
awk -v new="$NEW_VERSION" '
    !done && $0 ~ /^__version__[[:space:]]*=[[:space:]]*"/ {
        sub(/"[^"]*"/, "\"" new "\"")
        done = 1
    }
    { print }
' "$_init_file" > "$_init_file.tmp" && mv "$_init_file.tmp" "$_init_file"

if ! grep -q -E "^__version__[[:space:]]*=[[:space:]]*\"$NEW_VERSION\"" "$_init_file"; then
    echo "[specify] Error: failed to update version in $_init_file" >&2
    exit 1
fi

# Resync uv.lock
_lock_ok=false
if [ "$_run_uv_lock" = "true" ]; then
    if command -v uv >/dev/null 2>&1; then
        if _uv_out=$(uv lock 2>&1); then
            _lock_ok=true
        else
            echo "[specify] Warning: 'uv lock' failed; uv.lock may be stale: $_uv_out" >&2
        fi
    else
        echo "[specify] Warning: 'uv' not found; skipped 'uv lock' (uv.lock is now stale — run 'uv lock' manually)" >&2
    fi
fi

if [ "$_lock_ok" = "true" ]; then
    echo "[OK] Version bumped ${CURRENT_VERSION} -> ${NEW_VERSION} (pyproject.toml, src/monetils/__init__.py, uv.lock)" >&2
else
    echo "[OK] Version bumped ${CURRENT_VERSION} -> ${NEW_VERSION} (pyproject.toml, src/monetils/__init__.py)" >&2
fi
