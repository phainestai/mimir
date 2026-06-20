#!/usr/bin/env bash
# archive.sh — archive a completed sprint and reset factory/ for the next run.
#
# Usage: scripts/archive.sh <slug>
#
#   <slug>  URL-safe identifier for the sprint, e.g. "registration-1.0" or the
#           milestone slug. Becomes factory/archive/<slug>/.
#
# What moves:
#   factory/blackboard.md          → factory/archive/<slug>/blackboard.md
#   factory/blueprints/            → factory/archive/<slug>/blueprints/
#   factory/tasks/done/            → factory/archive/<slug>/tasks/done/
#   factory/tasks/rejected/        → factory/archive/<slug>/tasks/rejected/
#   factory/tasks/blocked/         → factory/archive/<slug>/tasks/blocked/
#   factory/logs/*.log *.jsonl     → factory/archive/<slug>/logs/
#   factory/RESULT.md (if present) → factory/archive/<slug>/RESULT.md
#
# What stays:  factory/README.md, factory/archive/ tree itself.
#
# After the move the script recreates a clean empty skeleton and removes
# stale git worktrees, then commits everything.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SLUG="${1:?usage: $0 <slug>}"

ARCHIVE_DIR="factory/archive/${SLUG}"

# ── Guards ────────────────────────────────────────────────────────────────────

_count_md() { find "$1" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' '; }

pending_count="$(_count_md factory/tasks/pending)"
claimed_count="$(_count_md factory/tasks/claimed)"

if (( pending_count > 0 )); then
  echo "error: factory/tasks/pending/ still has ${pending_count} task(s) — sprint not complete." >&2
  echo "       Finish or reject remaining tasks before archiving." >&2
  exit 1
fi

if (( claimed_count > 0 )); then
  echo "error: factory/tasks/claimed/ has ${claimed_count} task(s) — workers still running." >&2
  echo "       Wait for workers to finish or manually move claimed tasks before archiving." >&2
  exit 1
fi

if [[ -e "$ARCHIVE_DIR" ]]; then
  echo "error: archive '${ARCHIVE_DIR}' already exists — choose a different slug or remove it first." >&2
  exit 1
fi

# ── Archive ───────────────────────────────────────────────────────────────────

mkdir -p \
  "${ARCHIVE_DIR}/blueprints" \
  "${ARCHIVE_DIR}/tasks/done" \
  "${ARCHIVE_DIR}/tasks/rejected" \
  "${ARCHIVE_DIR}/tasks/blocked" \
  "${ARCHIVE_DIR}/logs"

echo "Archiving sprint '${SLUG}' → ${ARCHIVE_DIR}/"

# blackboard
if [[ -f factory/blackboard.md ]]; then
  mv factory/blackboard.md "${ARCHIVE_DIR}/blackboard.md"
  echo "  blackboard.md"
fi

# RESULT.md (optional sprint summary written by LE)
if [[ -f factory/RESULT.md ]]; then
  mv factory/RESULT.md "${ARCHIVE_DIR}/RESULT.md"
  echo "  RESULT.md"
fi

# blueprints
shopt -s nullglob
blueprint_files=(factory/blueprints/*.md)
shopt -u nullglob
if (( ${#blueprint_files[@]} > 0 )); then
  mv "${blueprint_files[@]}" "${ARCHIVE_DIR}/blueprints/"
  echo "  blueprints/ (${#blueprint_files[@]} files)"
fi

# tasks/done, rejected, blocked — move all contents (dirs for rejected)
for lane in done rejected blocked; do
  src="factory/tasks/${lane}"
  dst="${ARCHIVE_DIR}/tasks/${lane}"
  shopt -s nullglob dotglob
  lane_items=("${src}"/*)
  shopt -u nullglob dotglob
  if (( ${#lane_items[@]} > 0 )); then
    mv "${lane_items[@]}" "${dst}/"
    echo "  tasks/${lane}/ (${#lane_items[@]} item(s))"
  fi
done

# logs
shopt -s nullglob
log_files=(factory/logs/*.log factory/logs/*.jsonl)
shopt -u nullglob
if (( ${#log_files[@]} > 0 )); then
  mv "${log_files[@]}" "${ARCHIVE_DIR}/logs/"
  echo "  logs/ (${#log_files[@]} files)"
fi

# ── Reset clean skeleton ──────────────────────────────────────────────────────

echo ""
echo "Recreating clean factory skeleton..."

# Fresh blackboard stub
cat > factory/blackboard.md <<'BBEOF'
# Blackboard

## Current state

_Sprint: (not started)_

## Event log

BBEOF

# Ensure queue directories exist with .gitkeep so they are tracked
for dir in \
  factory/blueprints \
  factory/tasks/pending \
  factory/tasks/claimed \
  factory/tasks/done \
  factory/tasks/rejected \
  factory/tasks/blocked \
  factory/logs; do
  mkdir -p "$dir"
  touch "${dir}/.gitkeep"
done

# ── Worktree cleanup ──────────────────────────────────────────────────────────

echo ""
echo "Removing stale git worktrees..."

for role in feature-builder step-def-writer release-engineer manual-tester; do
  wt=".worktrees/${role}"
  if [[ -e "$wt" ]]; then
    git worktree remove --force "$wt" 2>/dev/null && echo "  removed ${wt}" || echo "  skipped ${wt} (already gone)"
  fi
done
git worktree prune
echo "  git worktree prune done"

# ── Commit ────────────────────────────────────────────────────────────────────

echo ""
echo "Committing archive..."

git add factory/ .worktrees/ 2>/dev/null || git add factory/
git commit -m "factory: archive ${SLUG}"

echo ""
echo "Done. factory/ is clean and ready for the next sprint."
echo "Archive: ${ARCHIVE_DIR}/"
