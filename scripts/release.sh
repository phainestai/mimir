#!/usr/bin/env bash
# release.sh — cut a semver GitHub release after all tasks are integrated.
#
# Usage: scripts/release.sh <semver> [--dry-run]
#
# Guards:
#   1. <semver> matches x.y.z (no v prefix in argument)
#   2. factory/tasks/pending/ and factory/tasks/claimed/ are empty
#   3. Every factory/tasks/done/*.md has "status: integrated"
#   4. The git tag v<semver> does not already exist
#
# On success (non-dry-run, on main):
#   - git tag v<semver>
#   - git push origin v<semver>
#   - gh release create v<semver> (triggers CI deploy to idle EB — see Makefile)
#
# Production promote remains manual: make swap

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SEMVER="${1:?usage: $0 <semver> [--dry-run]}"
DRY_RUN=0
[[ "${2:-}" == "--dry-run" ]] && DRY_RUN=1

TAG="v${SEMVER}"

if ! [[ "$SEMVER" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "error: semver '${SEMVER}' must match x.y.z (pass without 'v' prefix)" >&2
  exit 1
fi

pending_count="$(find factory/tasks/pending -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
claimed_count="$(find factory/tasks/claimed -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"

if (( pending_count > 0 )); then
  echo "error: factory/tasks/pending/ is not empty (${pending_count} task(s))" >&2
  exit 1
fi
if (( claimed_count > 0 )); then
  echo "error: factory/tasks/claimed/ is not empty (${claimed_count} task(s))" >&2
  exit 1
fi

not_integrated=()
for f in factory/tasks/done/*.md; do
  [[ -f "$f" ]] || continue
  status_val="$(rg -m1 '^status:[[:space:]]*' "$f" 2>/dev/null | sed 's/^status:[[:space:]]*//' | tr -d '"' || echo '')"
  if [[ "$status_val" != "integrated" ]]; then
    not_integrated+=("$(basename "$f") (status: ${status_val:-missing})")
  fi
done

if (( ${#not_integrated[@]} > 0 )); then
  echo "error: done/ tasks not integrated:" >&2
  printf '  %s\n' "${not_integrated[@]}" >&2
  exit 1
fi

if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "error: git tag '${TAG}' already exists" >&2
  exit 1
fi

current_branch="$(git symbolic-ref --short HEAD 2>/dev/null || echo 'DETACHED')"
if [[ "$current_branch" != "main" ]]; then
  echo "error: must be on 'main' (currently on '${current_branch}')" >&2
  exit 1
fi

echo "release.sh: all guards passed for ${SEMVER} (tag ${TAG})"

if [[ $DRY_RUN -eq 1 ]]; then
  echo "DRY RUN — would execute:"
  echo "  git tag ${TAG}"
  echo "  git push origin ${TAG}"
  echo "  gh release create ${TAG} --generate-notes"
  exit 0
fi

echo "Tagging and pushing …"
git tag "$TAG"
git push origin "$TAG"
gh release create "$TAG" --generate-notes

"$REPO_ROOT/scripts/bb-append.sh" "$(printf -- '- **%s %s** 🚀 (LE) cut release **%s** — CI deploy to idle EB starting' \
  "$(date +%Y-%m-%d)" "$(date +%H:%M:%S)" "$TAG")"

echo ""
echo "Release ${TAG} published. GitHub Actions will test, build, and deploy to idle EB."
echo "After staging review: make swap"
