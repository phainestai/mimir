#!/usr/bin/env bash
# done.sh — move a claimed task to done/ or blocked/.
#
# Usage:
#   scripts/done.sh <task-id>                      # requires # Result block; mv → done/
#   scripts/done.sh <task-id> --blocked "<reason>" # prepend # Blocked block; mv → blocked/
#
# Requires factory/tasks/claimed/<task-id>.md to exist.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TASK_ID="${1:?usage: $0 <task-id> [--blocked \"<reason>\"]}"
CLAIMED="factory/tasks/claimed/${TASK_ID}.md"
DONE="factory/tasks/done/${TASK_ID}.md"
BLOCKED="factory/tasks/blocked/${TASK_ID}.md"

[[ -f "$CLAIMED" ]] || {
  echo "error: task not in claimed/: ${TASK_ID}" >&2
  exit 1
}

if [[ "${2:-}" == "--blocked" ]]; then
  REASON="${3:?--blocked requires a reason string}"
  mkdir -p "factory/tasks/blocked"
  {
    printf '# Blocked\n\nreason: %s\n\n---\n\n' "$REASON"
    cat "$CLAIMED"
  } > "$BLOCKED"
  rm -f "$CLAIMED"
  "$REPO_ROOT/scripts/bb-append.sh" "$(printf -- '- **%s %s** 🔴 blocked **%s**: %s' \
    "$(date +%Y-%m-%d)" "$(date +%H:%M:%S)" "$TASK_ID" "$REASON")"
  echo "$(pwd)/${BLOCKED}"
else
  # Strict mode: require # Result block — no silent stub injection
  if ! rg -q '^# Result' "$CLAIMED" 2>/dev/null; then
    echo "error: task ${TASK_ID} has no '# Result' block — worker must fill it before marking done." >&2
    echo "       Use --blocked \"<reason>\" to route to blocked/ instead." >&2
    exit 1
  fi
  mv "$CLAIMED" "$DONE"
  echo "$(pwd)/${DONE}"
fi
