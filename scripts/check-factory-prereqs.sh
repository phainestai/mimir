#!/usr/bin/env bash
# check-factory-prereqs.sh — verify CLI tools for dark-factory.
#
# Usage:
#   scripts/check-factory-prereqs.sh           # fail on missing binaries; warn on auth/cursor
#   scripts/check-factory-prereqs.sh --strict  # also fail on gh auth / cursor-agent warnings

set -euo pipefail

STRICT=0
[[ "${1:-}" == "--strict" ]] && STRICT=1

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

missing=()
warn=()

check_cmd() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    printf '  ok  %s (%s)\n' "$name" "$(command -v "$name")"
    return 0
  fi
  missing+=("$name")
  printf '  MISSING  %s\n' "$name"
  return 1
}

echo "Dark-factory prerequisites:"

for c in git gh fswatch tmux rg python3 jq; do
  check_cmd "$c" || true
done

if command -v flock >/dev/null 2>&1; then
  printf '  ok  flock (%s)\n' "$(command -v flock)"
elif [[ -x "$(brew --prefix util-linux 2>/dev/null)/bin/flock" ]]; then
  flock_path="$(brew --prefix util-linux)/bin/flock"
  printf '  ok  flock (%s — add util-linux to PATH for shell use)\n' "$flock_path"
  warn+=("flock not on PATH (bb-append.sh resolves via brew --prefix util-linux)")
else
  missing+=("flock (util-linux)")
  printf '  MISSING  flock — run make provision or install util-linux\n'
fi

if command -v cursor-agent >/dev/null 2>&1; then
  printf '  ok  cursor-agent (%s)\n' "$(command -v cursor-agent)"
elif command -v cursor >/dev/null 2>&1; then
  printf '  ok  cursor (%s — factory.sh accepts cursor CLI)\n' "$(command -v cursor)"
else
  warn+=("cursor-agent or cursor not on PATH (install via Cursor IDE CLI)")
  printf '  WARN  cursor-agent / cursor not found\n'
fi

if command -v gh >/dev/null 2>&1; then
  if gh auth status >/dev/null 2>&1; then
    printf '  ok  gh auth\n'
  else
    warn+=("gh not authenticated — run: gh auth login")
    printf '  WARN  gh auth — run: gh auth login\n'
  fi
fi

if command -v watch >/dev/null 2>&1; then
  printf '  ok  watch (optional status pane)\n'
else
  printf '  note watch not installed (factory.sh uses sleep loop fallback)\n'
fi

echo ""
if (( ${#missing[@]} > 0 )); then
  echo "Missing required tools: ${missing[*]}"
  echo "Re-run: make provision"
  exit 1
fi

if (( ${#warn[@]} > 0 )); then
  echo "Manual steps (not installed by make provision):"
  for w in "${warn[@]}"; do
    echo "  - $w"
  done
  if (( STRICT == 1 )); then
    exit 1
  fi
fi

if (( ${#missing[@]} == 0 && ${#warn[@]} == 0 )); then
  echo "All dark-factory prerequisites satisfied."
fi

exit 0
