#!/usr/bin/env bash
# verify-result.sh — verify a claimed task's # Result block before moving to done/.
#
# Usage: scripts/verify-result.sh <task-id>
#
# Reads factory/tasks/claimed/<id>.md and checks:
#   1. A "# Result" block exists with non-empty status:, branch:, mr:, commit_sha:
#   2. The branch exists on origin (git ls-remote)
#   3. The PR is OPEN or MERGED (gh pr view)
#
# Exit 0 on success.
# Exit 2 on failure; reason written to stderr as "reason:<field>: <detail>".
#
# Requires: rg (ripgrep), git, gh, jq

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TASK_ID="${1:?usage: $0 <task-id>}"
CLAIMED="factory/tasks/claimed/${TASK_ID}.md"

[[ -f "$CLAIMED" ]] || {
  echo "error: task not in claimed/: ${TASK_ID}" >&2
  exit 1
}

if ! rg -q '^# Result' "$CLAIMED" 2>/dev/null; then
  echo "reason:result_block: no '# Result' section in ${CLAIMED}" >&2
  exit 2
fi

result_section="$(awk '/^# Result/{found=1; next} found{print}' "$CLAIMED")"

_field() {
  printf '%s\n' "$result_section" \
    | rg -m1 "^${1}:[[:space:]]*" \
    | sed "s/^${1}:[[:space:]]*//" \
    | tr -d '"' \
    | tr -d "'"
}

STATUS="$(_field status)"
BRANCH="$(_field branch)"
MR="$(_field mr)"
COMMIT_SHA="$(_field commit_sha)"

[[ -n "$STATUS" ]] || { echo "reason:status: field 'status' is empty" >&2; exit 2; }
[[ -n "$BRANCH" ]] || { echo "reason:branch: field 'branch' is empty" >&2; exit 2; }
[[ -n "$MR" ]]     || { echo "reason:mr: field 'mr' is empty" >&2; exit 2; }
[[ -n "$COMMIT_SHA" ]] || { echo "reason:commit_sha: field 'commit_sha' is empty" >&2; exit 2; }

# Monitoring tasks (release-engineer pipeline watch) skip PR verification
if [[ "$STATUS" == "monitoring" && "$MR" == "0" ]]; then
  echo "verify-result: ${TASK_ID} OK (monitoring task, mr=0)"
  exit 0
fi

if ! git ls-remote --exit-code origin "$BRANCH" >/dev/null 2>&1; then
  echo "reason:branch: branch '${BRANCH}' not found on origin" >&2
  exit 2
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "reason:mr: jq not found — install via: brew install jq" >&2
  exit 2
fi

pr_state="$(gh pr view "$MR" --json state -q .state 2>/dev/null || true)"
if [[ -z "$pr_state" ]]; then
  echo "reason:mr: could not fetch PR #${MR} state (gh pr view failed)" >&2
  exit 2
fi
if [[ "$pr_state" != "OPEN" && "$pr_state" != "MERGED" ]]; then
  echo "reason:mr: PR #${MR} state is '${pr_state}', expected OPEN or MERGED" >&2
  exit 2
fi

echo "verify-result: ${TASK_ID} OK (branch=${BRANCH} pr=#${MR} status=${STATUS})"
exit 0
