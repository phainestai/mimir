# Dark factory (`factory/`)

Mechanical scaffold for the **dark-factory** sprint factory on Mimir: milestone-driven LE + specialist workers via filesystem queue (`tasks/pending` → `claimed` → `done`), tmux + `fswatch`, and Cursor CLI.

## Canonical docs

| Topic | Location |
|--------|-----------|
| Process contract (phases 0–6) | [.cursor/skills/dark-factory/SKILL.md](../.cursor/skills/dark-factory/SKILL.md) |
| Worker prompts | [`prompts/`](../prompts/) (used by `scripts/factory.sh`) |
| LE watch loop | [`references/worker-protocol.md`](../references/worker-protocol.md) |
| CI/CD, staging vs prod | [`docs/architecture/SAO.md`](../docs/architecture/SAO.md) |
| Iteration protocol (PIT/MIN) | [`.cursor/rules/iteration-protocol.mdc`](../.cursor/rules/iteration-protocol.mdc) |

Mimir uses **GitHub** (`gh`) for milestones/issues/PRs — not GitLab (`glab`).

## Prerequisites

Installed by **`make provision`** (single command with Python app + factory CLIs).

Re-check anytime:

```bash
make factory-check   # strict — includes gh auth + cursor-agent
```

**Manual steps after first `make provision`** (cannot be automated):

- `gh auth login` — if GitHub CLI is new
- `cursor-agent` on PATH — install/update via [Cursor CLI](https://cursor.com/docs/cli)

On macOS, if `flock` is missing from PATH after provision, add:

```bash
export PATH="$(brew --prefix util-linux)/bin:$PATH"
```

Mockups for ingestion: `templates/mockups/` and `docs/ux/`.

## Commands (from repo root)

```bash
# Phase 0 — validate milestone, issues, tooling
./scripts/preflight.sh 'Your Milestone Title'

# Phase 3 — tmux factory (after LE has filled pending tasks)
./scripts/factory.sh 'Your-Milestone-Slug'
# Attach: tmux a -t mimir-Your-Milestone-Slug

# Merge worker PRs (LE)
./scripts/integrate.sh merge T-001

# Cut release after all tasks integrated (triggers CI → idle EB)
./scripts/release.sh 1.2.3

# Post-sprint archive
./scripts/archive.sh 'your-sprint-slug'
```

**Preflight flags:** `--allow-dirty`, `--allow-missing-featurefile-ref`

**Production promote** (manual, after staging review): `make swap` (see Makefile).

## Task queue lanes

| Directory | Meaning |
|-----------|---------|
| `tasks/pending/` | Waiting to be claimed |
| `tasks/claimed/` | In progress |
| `tasks/done/` | Awaiting LE review + `integrate.sh merge` |
| `tasks/blocked/` | Max attempts or verify-result failure |
| `tasks/rejected/<id>/` | Archived rejection snapshots |

## Maintainer verification

```bash
bash -n scripts/factory.sh scripts/preflight.sh scripts/claim.sh scripts/done.sh \
         scripts/reject.sh scripts/status.sh scripts/bb-append.sh \
         scripts/verify-result.sh scripts/integrate.sh scripts/release.sh \
         scripts/archive.sh scripts/rescue-result.sh
```
