#!/usr/bin/env bash
# rescue-result.sh — auto-fill an empty # Result block from git state.
#
# Usage: scripts/rescue-result.sh <task-id>
#
# Requires: git, gh, rg, jq

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TASK_ID="${1:?usage: $0 <task-id>}"
CLAIMED="factory/tasks/claimed/${TASK_ID}.md"
BLOCKED="factory/tasks/blocked/${TASK_ID}.md"

if [[ -f "$CLAIMED" ]]; then
  TARGET="$CLAIMED"
elif [[ -f "$BLOCKED" ]]; then
  TARGET="$BLOCKED"
else
  echo "rescue-result: task not in claimed/ or blocked/: ${TASK_ID}" >&2
  exit 1
fi

if rg -q '^# Result' "$TARGET" 2>/dev/null; then
  result_section="$(awk '/^# Result/{found=1; next} found{print}' "$TARGET")"
  _status="$(printf '%s\n' "$result_section" | rg -m1 '^status:[[:space:]]*' 2>/dev/null | sed 's/^status:[[:space:]]*//' | tr -d '"' || true)"
  _branch="$(printf '%s\n' "$result_section" | rg -m1 '^branch:[[:space:]]*' 2>/dev/null | sed 's/^branch:[[:space:]]*//' | tr -d '"' || true)"
  _mr="$(printf '%s\n' "$result_section" | rg -m1 '^mr:[[:space:]]*' 2>/dev/null | sed 's/^mr:[[:space:]]*//' | tr -d '"' || true)"
  _sha="$(printf '%s\n' "$result_section" | rg -m1 '^commit_sha:[[:space:]]*' 2>/dev/null | sed 's/^commit_sha:[[:space:]]*//' | tr -d '"' || true)"
  if [[ -n "$_status" && -n "$_branch" && -n "$_mr" && -n "$_sha" ]]; then
    echo "rescue-result: ${TASK_ID} already has complete # Result block — skipping"
    exit 0
  fi
  tmpfile="$(mktemp)"
  awk '/^# Result/{exit} {print}' "$TARGET" > "$tmpfile"
  mv "$tmpfile" "$TARGET"
fi

BRANCH="$(rg -m1 '^branch:[[:space:]]*' "$TARGET" 2>/dev/null \
          | sed 's/^branch:[[:space:]]*//' | tr -d '"' | tr -d "'")"

if [[ -z "$BRANCH" ]]; then
  echo "rescue-result: no branch: field in ${TARGET}" >&2
  exit 1
fi

COMMIT_SHA="$(git ls-remote origin "$BRANCH" 2>/dev/null | awk '{print $1}' | cut -c1-8 || true)"

MR="0"
if command -v gh >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
  MR="$(gh pr list --head "$BRANCH" --json number -q '.[0].number // 0' 2>/dev/null || echo 0)"
fi

STATUS="rescued"
[[ -n "$COMMIT_SHA" ]] || COMMIT_SHA="unknown"

printf '\n# Result\n\nstatus: %s\nbranch: %s\nmr: %s\ncommit_sha: %s\n\nAuto-filled by rescue-result.sh.\n' \
  "$STATUS" "$BRANCH" "$MR" "$COMMIT_SHA" >> "$TARGET"

echo "rescue-result: ${TASK_ID} → branch=${BRANCH} pr=#${MR} sha=${COMMIT_SHA}"

git add "$TARGET" 2>/dev/null || true
git commit -m "factory: rescue ${TASK_ID} (auto-filled empty Result block)" 2>/dev/null || true
