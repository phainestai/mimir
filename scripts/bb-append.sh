#!/usr/bin/env bash
# bb-append.sh — append one line to factory/blackboard.md under flock.
#
# Usage: scripts/bb-append.sh "<markdown-line>"
#
# Requires flock(1) from util-linux:
#   macOS:  brew install util-linux
#   Linux:  apt install util-linux (usually pre-installed)
#
# The line is written with a leading blank line for markdown list separation.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

LINE="${1:?usage: $0 \"<line>\"}"
LOCK="$REPO_ROOT/factory/.blackboard.lock"
BLACKBOARD="$REPO_ROOT/factory/blackboard.md"

# Resolve flock: on macOS util-linux is keg-only and may not be on PATH.
FLOCK_CMD=""
if command -v flock >/dev/null 2>&1; then
  FLOCK_CMD="flock"
elif [[ -x "$(brew --prefix util-linux 2>/dev/null)/bin/flock" ]]; then
  FLOCK_CMD="$(brew --prefix util-linux)/bin/flock"
else
  echo "error: flock not found — install via: brew install util-linux (macOS) or apt install util-linux (Linux)" >&2
  echo "       On macOS, also add to PATH: export PATH=\"\$(brew --prefix util-linux)/bin:\$PATH\"" >&2
  exit 1
fi

(
  "$FLOCK_CMD" -x 9
  printf '\n%s\n' "$LINE" >> "$BLACKBOARD"
) 9>"$LOCK"
