#!/usr/bin/env bash
# factory.sh — spawn the sprint factory for a given milestone.
#
# Usage:  scripts/factory.sh <milestone-name> [mgmt-branch]
#
# mgmt-branch defaults to the current branch (should be features/<milestone>).
# Run from repo root (or any cwd — script cds to repo root).
#
# Worktree model:
#   - Repo root stays on the MGMT branch (features/<milestone>) — LE home.
#     Factory state (tasks/, blackboard.md) is committed here only.
#   - Each worker role gets a git worktree under .worktrees/<role>/
#     so workers never need to checkout the mgmt branch or stash.
#   - .worktrees/ is in .gitignore; worktrees are pruned on teardown.
#
# Creates a tmux session named `huginn-<milestone>` with:
#   - one window per worker role, cwd = .worktrees/<role>/
#   - one window for the LE (cwd = repo root, mgmt branch)
#   - one window tailing the blackboard
#   - one window running status on a 2s interval (watch if available)
#
# Attach at the end. Detach with prefix-d, reattach with `tmux a -t huginn-<m>`.

set -euo pipefail

MILESTONE="${1:?usage: $0 <milestone-name>}"
MGMT_BRANCH="${2:-$(git symbolic-ref --short HEAD 2>/dev/null || echo 'features/gjallarhorn')}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SESSION="mimir-${MILESTONE}"

# Find a suitable Cursor CLI binary. The exact name varies across versions;
# adjust this if your install is different (see factory/README.md).
if command -v cursor-agent >/dev/null 2>&1; then
  CURSOR_BIN="cursor-agent"
elif command -v cursor >/dev/null 2>&1; then
  CURSOR_BIN="cursor"
else
  echo "error: cursor-agent (or cursor) not found on PATH" >&2
  exit 1
fi

# Per-role model defaults. Override with env vars when cost/quality tradeoffs
# differ for a specific sprint.
LE_MODEL="${FACTORY_LE_MODEL:-claude-opus-4-7-thinking-xhigh}"

role_model_default() {
  case "$1" in
    feature-builder)
      printf '%s\n' "${FACTORY_MODEL_FEATURE_BUILDER:-claude-4.6-sonnet-medium-thinking}"
      ;;
    step-def-writer)
      printf '%s\n' "${FACTORY_MODEL_STEP_DEF_WRITER:-}"
      ;;
    release-engineer)
      printf '%s\n' "${FACTORY_MODEL_RELEASE_ENGINEER:-}"
      ;;
    manual-tester)
      printf '%s\n' "${FACTORY_MODEL_MANUAL_TESTER:-}"
      ;;
    *)
      printf '%s\n' ""
      ;;
  esac
}

# Kill any existing session for this milestone so re-runs are idempotent.
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "session $SESSION exists — killing and restarting" >&2
  tmux kill-session -t "$SESSION"
fi

mkdir -p factory/{blueprints,tasks/{pending,claimed,blocked,done,rejected},logs}
mkdir -p .worktrees

# Ensure .worktrees is gitignored
if ! grep -qxF '.worktrees/' .gitignore 2>/dev/null; then
  echo '.worktrees/' >> .gitignore
fi

ROLES=(step-def-writer feature-builder release-engineer manual-tester)

# Create a worktree for each role on an orphan scratch branch.
# Workers check out their task branch inside the worktree when they claim a task.
# Retry up to 3 times so a transient lock doesn't silently kill a worker pane.
for role in "${ROLES[@]}"; do
  wt="$REPO_ROOT/.worktrees/$role"
  for _wt_try in 1 2 3; do
    [[ -d "$wt" ]] && break
    git worktree add "$wt" "$MGMT_BRANCH" --detach 2>/dev/null || true
    sleep 2
  done
  if [[ ! -d "$wt" ]]; then
    echo "error: could not create worktree for $role after 3 attempts — aborting" >&2
    exit 1
  fi
done

worker_loop() {
  local role="$1"
  local wt="$REPO_ROOT/.worktrees/$role"
  local model
  model="$(role_model_default "$role")"
  cat <<EOF
cd "$wt" || exit 1
WORKER_MODEL="$model"

# _process_pending — scan pending/ and claim+work any task matching this role.
# Called once at startup (so pre-existing tasks aren't missed) and on each fswatch event.
_process_pending() {
  local f id declared_role claimed_path task_branch
  local _skip_agent _rel_branch _existing _task_outcome _verify_reason
  local COMBINED_PROMPT _remediation _wt_copy
  for f in "$REPO_ROOT"/factory/tasks/pending/*.md; do
    [[ -f "\$f" ]] || continue
    id="\$(basename "\$f" .md)"
    declared_role="\$(rg -m1 '^role:[[:space:]]*' "\$f" 2>/dev/null | sed 's/^role:[[:space:]]*//')"
    [[ "\$declared_role" == "$role" ]] || continue
    # claim.sh runs in the REPO ROOT (mgmt branch) so factory state commits land there
    if claimed_path="\$($REPO_ROOT/scripts/claim.sh "\$id" "$role" 2>/dev/null)"; then
      echo "[\$(date +%H:%M:%S)] $role claimed \$id"
      "$REPO_ROOT/scripts/bb-append.sh" "\$(printf -- '- **%s %s** 🔧 **%s** claimed **%s**' "\$(date +%Y-%m-%d)" "\$(date +%H:%M:%S)" "$role" "\$id")"
      # Switch this worktree to the task's feature branch, always based on a
      # fresh origin/main (fixes #80: workers were branching off the dirty
      # worktree tip, dragging rejected commits into the new branch).
      task_branch="\$(rg -m1 '^branch:[[:space:]]*' "\$claimed_path" 2>/dev/null | sed 's/^branch:[[:space:]]*//')"
      if [[ -n "\$task_branch" ]]; then
        git fetch origin 2>/dev/null || true
        git checkout "\$task_branch" 2>/dev/null \
          || git checkout -b "\$task_branch" origin/main 2>/dev/null \
          || true
      fi
      # release-engineer guard: skip cursor-agent if release branch pipeline already exists
      _skip_agent=0
      if [[ "$role" == "release-engineer" ]]; then
        _rel_branch="\$(rg -m1 '^branch:[[:space:]]*' "\$claimed_path" 2>/dev/null | sed 's/^branch:[[:space:]]*//')"
        if [[ -n "\$_rel_branch" ]]; then
          _existing="\$(cd "$REPO_ROOT" && gh run list --branch "\$_rel_branch" --limit 1 --json status -q '.[0].status' 2>/dev/null || true)"
          if [[ "\$_existing" == "in_progress" || "\$_existing" == "queued" || "\$_existing" == "completed" || "\$_existing" == "success" ]]; then
            echo "[\$(date +%H:%M:%S)] release-engineer: pipeline already \$_existing for \$_rel_branch — skipping agent"
            "$REPO_ROOT/scripts/bb-append.sh" "\$(printf -- '- **%s** ⏭ release-engineer skipped (pipeline already %s)' "\$(date +%H:%M:%S)" "\$_existing")"
            _skip_agent=1
          fi
        fi
      fi
      _task_outcome="blocked"
      if [[ \$_skip_agent -eq 1 ]]; then
        # Pipeline already running — inject a minimal Result block so done.sh accepts
        # the file without running verify-result.sh (no MR was created this invocation).
        printf '\n\n# Result\n\nstatus: monitoring\nbranch: "%s"\nmr: "0"\ncommit_sha: "monitoring"\n' "\$task_branch" >> "\$claimed_path"
        "$REPO_ROOT/scripts/done.sh" "\$id" 2>/dev/null || true
        "$REPO_ROOT/scripts/bb-append.sh" "\$(printf -- '- **%s %s** ✅ **release-engineer** done **%s** (pipeline already running — monitoring)' "\$(date +%Y-%m-%d)" "\$(date +%H:%M:%S)" "\$id")"
        _task_outcome="done"
      else
        # Include LE remediation overlay if present alongside the claimed task
        _remediation=""
        if [[ -f "$REPO_ROOT/factory/tasks/claimed/\${id}.remediation.md" ]]; then
          _remediation="\$(cat "$REPO_ROOT/factory/tasks/claimed/\${id}.remediation.md")"
        fi
        if [[ -n "\$_remediation" ]]; then
          COMBINED_PROMPT="\$(printf '%s\n\n---\n\n%s\n\n---\n\n## LE Remediation\n\n%s' "\$(cat $REPO_ROOT/prompts/${role}.md)" "\$(cat "\$claimed_path")" "\$_remediation")"
        else
          COMBINED_PROMPT="\$(printf '%s\n\n---\n\n%s' "\$(cat $REPO_ROOT/prompts/${role}.md)" "\$(cat "\$claimed_path")")"
        fi
        CURSOR_ARGS=(--print --yolo --output-format stream-json --stream-partial-output --workspace "\$wt")
        if [[ -n "\$WORKER_MODEL" ]]; then
          CURSOR_ARGS=(--model "\$WORKER_MODEL" "\${CURSOR_ARGS[@]}")
        fi
        $CURSOR_BIN \\
          "\${CURSOR_ARGS[@]}" \\
          "\$COMBINED_PROMPT" \\
          2>&1 | tee -a "$REPO_ROOT/factory/logs/${role}.jsonl" \
               | jq -r 'select(.type=="text") | .text' 2>/dev/null \
               | tee -a "$REPO_ROOT/factory/logs/${role}.log"
        # Layer A: sync Result block from worktree copy → repo-root copy.
        # Workers write to \$wt/factory/tasks/claimed/T-NNN.md (their workspace); verify-result.sh
        # reads \$REPO_ROOT/factory/tasks/claimed/T-NNN.md — different files in different worktrees.
        _wt_copy="$wt/factory/tasks/claimed/\${id}.md"
        if [[ -f "\$_wt_copy" ]] && rg -q '^# Result' "\$_wt_copy" 2>/dev/null; then
          if ! rg -q '^# Result' "\$claimed_path" 2>/dev/null; then
            awk '/^# Result/{found=1} found{print}' "\$_wt_copy" >> "\$claimed_path"
            echo "[\$(date +%H:%M:%S)] [sync] copied # Result block from worktree → claimed/"
          fi
        fi
        # Layer B: unconditionally run rescue-result.sh — it no-ops if all fields are
        # already filled, and auto-fills from git state otherwise (fixes #79: agent
        # consistently writes the # Result header but leaves fields empty).
        echo "[\$(date +%H:%M:%S)] [rescue] running rescue-result.sh (always)"
        "$REPO_ROOT/scripts/rescue-result.sh" "\$id" 2>/dev/null || true
        if _verify_reason="\$($REPO_ROOT/scripts/verify-result.sh "\$id" 2>&1 1>/dev/null)"; then
          "$REPO_ROOT/scripts/done.sh" "\$id" 2>/dev/null || true
          "$REPO_ROOT/scripts/bb-append.sh" "\$(printf -- '- **%s %s** ✅ **%s** done **%s**' "\$(date +%Y-%m-%d)" "\$(date +%H:%M:%S)" "$role" "\$id")"
          _task_outcome="done"
        else
          "$REPO_ROOT/scripts/done.sh" "\$id" --blocked "\$_verify_reason" 2>/dev/null || true
          # done.sh --blocked already appends to blackboard; _task_outcome stays "blocked"
        fi
      fi
      (cd "$REPO_ROOT" && git pull --rebase 2>/dev/null || true; \
        git diff --name-only --diff-filter=U 2>/dev/null | xargs -r git checkout --theirs -- 2>/dev/null || true; \
        git add factory/tasks/ factory/blackboard.md && git commit -m "factory: \${_task_outcome} \$id" && git push) 2>&1 | tee -a "$REPO_ROOT/factory/logs/${role}.log" || true
      if [[ "$role" == "release-engineer" && "\$_task_outcome" == "done" ]]; then
        for _i in \$(seq 1 40); do
          sleep 60
          _status="\$(cd "$REPO_ROOT" && gh run list --limit 1 --json status,conclusion -q '.[0].status + "/" + (.[0].conclusion // "")' 2>/dev/null || true)"
          "$REPO_ROOT/scripts/bb-append.sh" "\$(printf -- '- **%s** 🔄 pipeline: %s' "\$(date +%H:%M:%S)" "\$_status")"
          if [[ "\$_status" == *"completed/success"* ]]; then
            _staging="\$(make -s eb-status 2>/dev/null | rg 'mimir-idle' || echo 'see idle EB CNAME via make eb-status')"
            "$REPO_ROOT/scripts/bb-append.sh" "\$(printf -- '- **%s** 🌐 **staging ready:** %s' "\$(date +%H:%M:%S)" "\$_staging")"
            break
          elif [[ "\$_status" == *"completed/failure"* ]]; then
            _url="\$(gh run list --limit 1 --json url -q '.[0].url' 2>/dev/null || echo 'gh run list')"
            "$REPO_ROOT/scripts/bb-append.sh" "\$(printf -- '- **%s** ❌ **workflow FAILED** — %s' "\$(date +%H:%M:%S)" "\$_url")"
            break
          fi
        done
      fi
    fi
  done
}

# Initial scan — process any tasks already sitting in pending/ before fswatch starts.
# fswatch -1 is edge-triggered and misses pre-existing files on restart.
_process_pending
# Event loop — wake on filesystem events and re-scan
while :; do
  fswatch -1 "$REPO_ROOT/factory/tasks/pending" >/dev/null 2>&1 || true
  _process_pending
done
EOF
}

# LE window — autonomous agent loop on mgmt branch, reviews done/ tasks
LE_LOOP=$(cat <<'LEEOF'
cd "REPO_ROOT_PLACEHOLDER" && git checkout MGMT_PLACEHOLDER 2>/dev/null || true

le_run() {
  local reason="$1"
  PROMPT="$(cat REPO_ROOT_PLACEHOLDER/prompts/lead-engineer.md)

---

WAKE REASON: $reason
MILESTONE: MILESTONE_PLACEHOLDER

FACTORY STATE:
$(cat REPO_ROOT_PLACEHOLDER/factory/blackboard.md)

PENDING:  $(ls REPO_ROOT_PLACEHOLDER/factory/tasks/pending/  2>/dev/null | tr '\n' ' ')
CLAIMED:  $(ls REPO_ROOT_PLACEHOLDER/factory/tasks/claimed/  2>/dev/null | tr '\n' ' ')
DONE:     $(ls REPO_ROOT_PLACEHOLDER/factory/tasks/done/     2>/dev/null | tr '\n' ' ')
REJECTED: $(ls REPO_ROOT_PLACEHOLDER/factory/tasks/rejected/ 2>/dev/null | tr '\n' ' ')
BLOCKED:  $(ls REPO_ROOT_PLACEHOLDER/factory/tasks/blocked/  2>/dev/null | tr '\n' ' ')
WORKTREE_ROOT: REPO_ROOT_PLACEHOLDER/.worktrees

OPEN GITHUB ISSUES (milestone):
$(gh issue list --milestone "MILESTONE_PLACEHOLDER" --state all 2>/dev/null | head -40)

RECENT DONE/REJECTED/BLOCKED FILES:
$(ls -t REPO_ROOT_PLACEHOLDER/factory/tasks/done/ REPO_ROOT_PLACEHOLDER/factory/tasks/rejected/ REPO_ROOT_PLACEHOLDER/factory/tasks/blocked/ 2>/dev/null | head -10 | while read f; do echo "=== $f ==="; cat "REPO_ROOT_PLACEHOLDER/factory/tasks/done/$f" "REPO_ROOT_PLACEHOLDER/factory/tasks/rejected/$f" "REPO_ROOT_PLACEHOLDER/factory/tasks/blocked/$f" 2>/dev/null | tail -20; done)"
  CURSOR_BIN_PLACEHOLDER \
    --model "LE_MODEL_PLACEHOLDER" \
    --print \
    --yolo \
    --output-format stream-json \
    --stream-partial-output \
    --workspace "REPO_ROOT_PLACEHOLDER" \
    "$PROMPT" \
    2>&1 | tee -a "REPO_ROOT_PLACEHOLDER/factory/logs/le.jsonl" \
         | jq -r 'select(.type=="text") | .text' 2>/dev/null \
         | tee -a "REPO_ROOT_PLACEHOLDER/factory/logs/le.log"
  (cd "REPO_ROOT_PLACEHOLDER" && git pull --rebase 2>/dev/null || true; \
    git diff --name-only --diff-filter=U 2>/dev/null | xargs -r git checkout --theirs -- 2>/dev/null || true; \
    git add factory/ && git commit -m "factory: LE pass ($reason)" && git push) 2>/dev/null || true
}

# Startup scan — ingest new issues, review any existing done/ tasks
le_run "startup"

# Event-driven: wake on done/ or rejected/ changes; also poll every 5 min
while :; do
  fswatch -1 -r \
    "REPO_ROOT_PLACEHOLDER/factory/tasks/done" \
    "REPO_ROOT_PLACEHOLDER/factory/tasks/rejected" \
    "REPO_ROOT_PLACEHOLDER/factory/tasks/blocked" \
    2>/dev/null &
  FSWATCH_PID=$!
  # Also set a 5-minute timeout so we poll GitHub periodically
  ( sleep 300 && kill $FSWATCH_PID 2>/dev/null ) &
  TIMER_PID=$!
  wait $FSWATCH_PID 2>/dev/null
  kill $TIMER_PID 2>/dev/null
  le_run "done/rejected change or 5-min poll"
done
LEEOF
)
LE_LOOP="${LE_LOOP//REPO_ROOT_PLACEHOLDER/$REPO_ROOT}"
LE_LOOP="${LE_LOOP//MGMT_PLACEHOLDER/$MGMT_BRANCH}"
LE_LOOP="${LE_LOOP//CURSOR_BIN_PLACEHOLDER/$CURSOR_BIN}"
LE_LOOP="${LE_LOOP//LE_MODEL_PLACEHOLDER/$LE_MODEL}"
LE_LOOP="${LE_LOOP//MILESTONE_PLACEHOLDER/$MILESTONE}"
tmux new-session -d -s "$SESSION" -n "le" "bash -c $(printf '%q' "$LE_LOOP"); bash"

for role in "${ROLES[@]}"; do
  tmux new-window -t "$SESSION" -n "$role" \
    "$(worker_loop "$role"); bash"
done

tmux new-window -t "$SESSION" -n "blackboard" \
  "cd \"$REPO_ROOT\" && tail -F factory/blackboard.md; bash"

if command -v watch >/dev/null 2>&1; then
  STATUS_LOOP="watch -n 2 \"$REPO_ROOT/scripts/status.sh\""
else
  STATUS_LOOP="while sleep 2; do clear; \"$REPO_ROOT/scripts/status.sh\"; done"
fi

tmux new-window -t "$SESSION" -n "status" \
  "cd \"$REPO_ROOT\" && $STATUS_LOOP; bash"

tmux select-window -t "$SESSION:le"

echo "factory spawned. Attach with:"
echo "  tmux a -t $SESSION"
echo
echo "Or detach with prefix-d and reattach later."
echo
echo "Worktrees: $(git worktree list --porcelain | grep -c 'worktree') active"
echo "To clean up worktrees after the sprint: git worktree prune"
