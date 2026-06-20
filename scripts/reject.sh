#!/usr/bin/env bash
# reject.sh — archive a task and auto-requeue (bump attempt:) or
#             route to factory/tasks/blocked/ after FACTORY_MAX_ATTEMPTS.
#
# Usage: scripts/reject.sh <task-id> "<reason>"
# Looks for factory/tasks/done/<id>.md or factory/tasks/claimed/<id>.md

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TASK_ID="${1:?usage: $0 <task-id> \"reason\"}"
REASON="${2:?usage: $0 <task-id> \"reason\"}"
MAX_ATTEMPTS="${FACTORY_MAX_ATTEMPTS:-3}"

mkdir -p "factory/tasks/rejected/${TASK_ID}"
TS="$(date +%Y%m%d-%H%M%S)"
LOG="factory/tasks/rejected/${TASK_ID}/${TS}.txt"

for src in "factory/tasks/done/${TASK_ID}.md" "factory/tasks/claimed/${TASK_ID}.md"; do
  if [[ -f "$src" ]]; then
    # Archive original content with rejection header
    {
      echo "reason: ${REASON}"
      echo "---"
      cat "$src"
    } >"$LOG"
    rm -f "$src"
    echo "Archived to ${LOG}"

    # Parse current attempt from original frontmatter (lines 3+ of LOG skip the header)
    current_attempt="$(tail -n +3 "$LOG" | awk '/^---/{p=!p;next} p && /^attempt:/{print $2; exit}')"
    current_attempt="${current_attempt:-1}"
    next_attempt=$(( current_attempt + 1 ))

    if (( next_attempt <= MAX_ATTEMPTS )); then
      # Strip the Result block (always at end) and write a fresh pending task.
      # Note: use a named variable other than "log" to avoid shadowing awk's built-in log().
      pending_file="factory/tasks/pending/${TASK_ID}.md"
      {
        _attempt_injected=0
        while IFS= read -r _line; do
          if [[ "$_line" =~ ^attempt:[[:space:]]* && $_attempt_injected -eq 0 ]]; then
            printf 'attempt: %s\n' "$next_attempt"
            printf 'previous_attempt: %s\n' "$LOG"
            _attempt_injected=1
          else
            printf '%s\n' "$_line"
          fi
        done < <(tail -n +3 "$LOG" | awk '/^## Result|^# Result/{exit} {print}')
      } > "$pending_file"
      echo "Requeued as ${pending_file} (attempt ${next_attempt}/${MAX_ATTEMPTS})"
      "$REPO_ROOT/scripts/bb-append.sh" "$(printf -- '- **%s %s** 🔁 requeued **%s** attempt %s/%s: %s' \
        "$(date +%Y-%m-%d)" "$(date +%H:%M:%S)" "$TASK_ID" "$next_attempt" "$MAX_ATTEMPTS" "$REASON")"
    else
      # Max attempts exhausted — route to blocked/
      mkdir -p "factory/tasks/blocked"
      blocked_file="factory/tasks/blocked/${TASK_ID}.md"
      {
        printf -- '# Blocked\n\nreason: %s\nlast_archive: %s\nattempts_exhausted: %s\n\n---\n\n' \
          "$REASON" "$LOG" "$MAX_ATTEMPTS"
        tail -n +3 "$LOG"
      } > "$blocked_file"
      echo "Blocked at ${blocked_file} after ${MAX_ATTEMPTS} attempt(s)"
      "$REPO_ROOT/scripts/bb-append.sh" "$(printf -- '- **%s %s** 🚫 blocked **%s** after %s attempt(s): %s' \
        "$(date +%Y-%m-%d)" "$(date +%H:%M:%S)" "$TASK_ID" "$MAX_ATTEMPTS" "$REASON")"
    fi

    exit 0
  fi
done

echo "error: task not in done/ or claimed/: ${TASK_ID}" >&2
exit 1
