#!/usr/bin/env bash
# claim.sh — atomically move a pending task to claimed if role and deps match.
#
# Usage: scripts/claim.sh <task-id> <role>
# Stdout: absolute path to claimed file on success.
# Exit 1 if race, wrong role, missing deps, or pending file missing.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TASK_ID="${1:?usage: $0 <task-id> <role>}"
ROLE="${2:?usage: $0 <task-id> <role>}"

PENDING="factory/tasks/pending/${TASK_ID}.md"
CLAIMED="factory/tasks/claimed/${TASK_ID}.md"

[[ -f "$PENDING" ]] || exit 1

file_role="$(rg -m1 '^role:[[:space:]]*' "$PENDING" | sed 's/^role:[[:space:]]*//' | tr -d '\r')"
[[ -n "$file_role" ]] || exit 1
[[ "$file_role" == "$ROLE" ]] || exit 1

deps=()
while IFS= read -r line; do
  [[ -n "$line" ]] && deps+=("$line")
done < <(awk '
BEGIN { mode=0 }
/^depends_on:[[:space:]]*\[\][[:space:]]*$/ { exit }
/^depends_on:[[:space:]]*\[[[:space:]]*[^]]*[[:space:]]*\][[:space:]]*$/ {
  line=$0
  sub(/^depends_on:[[:space:]]*\[/,"",line)
  sub(/\][[:space:]]*$/,"",line)
  n=split(line,a,",")
  for (i=1;i<=n;i++) {
    gsub(/^[[:space:]]+|[[:space:]]+$/,"",a[i])
    if (a[i] != "") print a[i]
  }
  exit
}
/^depends_on:[[:space:]]*$/ { mode=1; next }
mode==1 && /^[[:space:]]*-[[:space:]]/ {
  id=$0
  sub(/^[[:space:]]*-[[:space:]]*/,"",id)
  sub(/^["]+|["]+$/,"",id)
  print id
  next
}
mode==1 && /^[^[:space:]#]/ && $0 !~ /^---$/ { mode=0 }
' "$PENDING")

for ((i = 0; i < ${#deps[@]}; i++)); do
  d="${deps[i]}"
  [[ -f "factory/tasks/done/${d}.md" ]] || exit 1
done

mv "$PENDING" "$CLAIMED"
# Also move any LE remediation overlay so the worker sees it in their combined prompt
PENDING_REMEDIATION="factory/tasks/pending/${TASK_ID}.remediation.md"
CLAIMED_REMEDIATION="factory/tasks/claimed/${TASK_ID}.remediation.md"
[[ -f "$PENDING_REMEDIATION" ]] && mv "$PENDING_REMEDIATION" "$CLAIMED_REMEDIATION" || true
echo "$(pwd)/${CLAIMED}"
