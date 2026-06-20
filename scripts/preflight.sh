#!/usr/bin/env bash
# preflight.sh — Phase 0 dry gate for dark-factory (tools, git clean, milestone, issues).
#
# Usage: scripts/preflight.sh [--allow-dirty] [--allow-missing-featurefile-ref] <milestone-title>
#
# Milestone must match GitHub milestone title for `gh issue list --milestone`.
# By default, each issue title/description must mention at least one path like
# docs/features/.../*.feature. Pass --allow-missing-featurefile-ref to warn-only
# when some issues omit that (e.g. pure infra/tech tasks); default stays strict.

set -euo pipefail

ALLOW_DIRTY=false
ALLOW_MISSING_FEATUREFILE_REF=false
ARGS=()
for arg in "$@"; do
  case "$arg" in
    --allow-dirty) ALLOW_DIRTY=true ;;
    --allow-missing-featurefile-ref) ALLOW_MISSING_FEATUREFILE_REF=true ;;
    *) ARGS+=("$arg") ;;
  esac
done

MILESTONE="${ARGS[0]:?usage: $0 [--allow-dirty] <milestone-title>}"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "error: missing command: $1" >&2
    exit 1
  }
}

for c in git gh fswatch tmux rg python3; do require_cmd "$c"; done

if ! command -v cursor-agent >/dev/null 2>&1 && ! command -v cursor >/dev/null 2>&1; then
  echo "error: need cursor-agent or cursor on PATH" >&2
  exit 1
fi

command -v jq >/dev/null 2>&1 || echo "warn: jq not on PATH (optional)" >&2
command -v watch >/dev/null 2>&1 || echo "warn: watch not on PATH (factory.sh falls back to sleep loop)" >&2

if [[ "$ALLOW_DIRTY" != true ]] && [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
  echo "error: git working tree not clean (commit/stash or pass --allow-dirty)" >&2
  exit 1
fi

MOCKS_FOUND=false
if [[ -d templates/mockups ]] && [[ -n "$(find templates/mockups -name '*.html' 2>/dev/null | head -1)" ]]; then
  MOCKS_FOUND=true
fi
if [[ "$MOCKS_FOUND" != true ]] && [[ -d docs/ux ]] && [[ -n "$(find docs/ux -name '*.drawio' 2>/dev/null | head -1)" ]]; then
  MOCKS_FOUND=true
fi
if [[ "$MOCKS_FOUND" != true ]]; then
  echo "warn: no mockups under templates/mockups/ or docs/ux/"
fi

ISSUES_JSON="$(gh issue list --milestone "$MILESTONE" --state all --json number,title,body --limit 500)" || {
  echo "error: gh issue list failed — check milestone title and auth (gh auth login)" >&2
  exit 1
}

if [[ "$ALLOW_MISSING_FEATUREFILE_REF" == true ]]; then
  export PREFLIGHT_ALLOW_MISSING_FEATUREFILE_REF=1
else
  unset PREFLIGHT_ALLOW_MISSING_FEATUREFILE_REF
fi

printf '%s' "$ISSUES_JSON" | python3 -c '
import json, os, re, sys

allow_missing = os.environ.get("PREFLIGHT_ALLOW_MISSING_FEATUREFILE_REF") == "1"

try:
    issues = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print("error: gh did not return valid JSON", e, file=sys.stderr)
    sys.exit(1)
if not isinstance(issues, list) or len(issues) == 0:
    print("error: no issues in milestone (title mismatch or empty milestone)", file=sys.stderr)
    sys.exit(1)
pat = re.compile(r"docs/features/[^\s\)]+\.feature")
missing = []
for i in issues:
    title = i.get("title") or ""
    desc = i.get("body") or ""
    body = title + "\n" + desc
    if not pat.search(body):
        missing.append(str(i.get("number", "?")))
if missing:
    msg = "issues missing docs/features/.../*.feature in title or body: " + ", ".join(missing)
    if allow_missing:
        print("warn:", msg, "(allowed by --allow-missing-featurefile-ref)", file=sys.stderr)
    else:
        print("error:", msg, file=sys.stderr)
        sys.exit(1)
    print("preflight ok:", len(issues), "issue(s);", len(missing), "without feature path (waived)")
else:
    print("preflight ok:", len(issues), "issue(s); feature paths referenced")
'
unset PREFLIGHT_ALLOW_MISSING_FEATUREFILE_REF 2>/dev/null || true
