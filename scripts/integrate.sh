#!/usr/bin/env bash
# integrate.sh — LE tool for reviewing and merging worker task branches.
#
# Usage:
#   scripts/integrate.sh <id>          # diff review (read-only)
#   scripts/integrate.sh merge <id>    # merge the PR via gh, mark task as integrated
#
# Requires: git, gh, jq, rg

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

MODE="review"
if [[ "${1:-}" == "merge" ]]; then
  MODE="merge"
  TASK_ID="${2:?usage: $0 merge <task-id>}"
else
  TASK_ID="${1:?usage: $0 <task-id> | $0 merge <task-id>}"
fi

DONE_FILE="factory/tasks/done/${TASK_ID}.md"

[[ -f "$DONE_FILE" ]] || {
  echo "error: task not in done/: ${TASK_ID}" >&2
  exit 1
}

result_section="$(awk '/^# Result/{found=1; next} found{print}' "$DONE_FILE")"

_field() {
  printf '%s\n' "$result_section" \
    | rg -m1 "^${1}:[[:space:]]*" \
    | sed "s/^${1}:[[:space:]]*//" \
    | tr -d '"' \
    | tr -d "'"
}

BRANCH="$(_field branch)"
MR="$(_field mr)"
ROLE="$(rg -m1 '^role:[[:space:]]*' "$DONE_FILE" 2>/dev/null | sed 's/^role:[[:space:]]*//' || echo '')"

[[ -n "$BRANCH" ]] || { echo "error: 'branch' field missing in ${DONE_FILE}" >&2; exit 1; }
[[ -n "$MR" ]]     || { echo "error: 'mr' field missing in ${DONE_FILE}" >&2; exit 1; }

WORKTREE="$REPO_ROOT/.worktrees/${ROLE}"

if [[ "$MODE" == "review" ]]; then
  echo "=== integrate: ${TASK_ID} (review) ==="
  echo "Worktree : ${WORKTREE}"
  echo "Branch   : ${BRANCH}"
  echo "PR       : #${MR}"
  echo ""

  if [[ -d "$WORKTREE" ]]; then
    echo "--- git log (${BRANCH} vs main) ---"
    git -C "$WORKTREE" log --oneline "main..${BRANCH}" 2>/dev/null || \
      echo "(worktree not on branch ${BRANCH})"
    echo ""
    echo "--- git diff --stat (main...${BRANCH}) ---"
    git -C "$WORKTREE" diff --stat "main...${BRANCH}" 2>/dev/null || true
  else
    echo "(worktree ${WORKTREE} not present)"
    echo "  git log --oneline main..${BRANCH}"
    echo "  git diff --stat main...${BRANCH}"
  fi
  exit 0
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "error: jq required for merge mode" >&2
  exit 1
fi

echo "=== integrate merge: ${TASK_ID} ==="
echo "PR #${MR}  branch ${BRANCH}"

pr_json="$(gh pr view "$MR" --json state,mergeable,mergeStateStatus 2>/dev/null)"
pr_state="$(printf '%s\n' "$pr_json" | jq -r '.state // empty')"
mergeable="$(printf '%s\n' "$pr_json" | jq -r '.mergeable // empty')"
merge_state="$(printf '%s\n' "$pr_json" | jq -r '.mergeStateStatus // empty')"

if [[ "$pr_state" == "MERGED" ]]; then
  echo "PR #${MR} is already merged — updating task status only."
else
  if [[ "$mergeable" != "MERGEABLE" && "$merge_state" != "CLEAN" ]]; then
    echo "error: PR #${MR} not mergeable (mergeable='${mergeable}', mergeStateStatus='${merge_state}')" >&2
    exit 1
  fi
  echo "Merging PR #${MR} (squash, delete branch) …"
  gh pr merge "$MR" --squash --delete-branch --yes
  echo "Merged."
fi

if rg -q '^status:' "$DONE_FILE" 2>/dev/null; then
  TMP="$(mktemp)"
  awk '
    /^# Result/{in_result=1}
    in_result && /^status:/ && !done { print "status: integrated"; done=1; next }
    { print }
  ' "$DONE_FILE" > "$TMP"
  mv "$TMP" "$DONE_FILE"
else
  printf '\nstatus: integrated\n' >> "$DONE_FILE"
fi

"$REPO_ROOT/scripts/bb-append.sh" "$(printf -- '- **%s %s** 🔀 (LE) merged **%s** via #%s → integrated' \
  "$(date +%Y-%m-%d)" "$(date +%H:%M:%S)" "$TASK_ID" "$MR")"

echo "Task ${TASK_ID} marked status: integrated."
