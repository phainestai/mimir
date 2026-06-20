#!/usr/bin/env bash
# status.sh — factory queue counts + sample IDs.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

count_md() {
  local dir="$1"
  local n=0
  local f
  shopt -s nullglob
  for f in "${dir}"/*.md; do
    [[ -f "$f" ]] || continue
    ((n++)) || true
  done
  shopt -u nullglob
  echo "$n"
}

sample_ids() {
  local dir="$1"
  local max="${2:-8}"
  local f n=0
  shopt -s nullglob
  for f in "${dir}"/*.md; do
    [[ -f "$f" ]] || continue
    printf '%s ' "$(basename "$f" .md)"
    ((++n >= max)) && break
  done
  shopt -u nullglob
  echo
}

echo "pending:  $(count_md factory/tasks/pending)  $(sample_ids factory/tasks/pending)"
echo "claimed:  $(count_md factory/tasks/claimed)  $(sample_ids factory/tasks/claimed)"
echo "blocked:  $(count_md factory/tasks/blocked)  $(sample_ids factory/tasks/blocked)"
echo "done:     $(count_md factory/tasks/done)     $(sample_ids factory/tasks/done)"

rej="$(find factory/tasks/rejected -mindepth 2 -type f 2>/dev/null | wc -l | tr -d ' ')"
echo "rejected archive files: ${rej} (under factory/tasks/rejected/<id>/)"

# RELEASE-READY: yes when pending+claimed=0 and every done/*.md has status: integrated
_pending="$(count_md factory/tasks/pending)"
_claimed="$(count_md factory/tasks/claimed)"
_done_total="$(count_md factory/tasks/done)"
_done_integrated=0
if (( _done_total > 0 )); then
  shopt -s nullglob
  for _f in factory/tasks/done/*.md; do
    _s="$(rg -m1 '^status:[[:space:]]*' "$_f" 2>/dev/null | sed 's/^status:[[:space:]]*//' | tr -d '"' || echo '')"
    [[ "$_s" == "integrated" ]] && (( _done_integrated++ )) || true
  done
  shopt -u nullglob
fi
if (( _pending == 0 && _claimed == 0 && _done_total > 0 && _done_integrated == _done_total )); then
  echo "RELEASE-READY: yes  (run: scripts/release.sh <semver>)"
else
  echo "RELEASE-READY: no   (pending=${_pending} claimed=${_claimed} integrated=${_done_integrated}/${_done_total})"
fi
