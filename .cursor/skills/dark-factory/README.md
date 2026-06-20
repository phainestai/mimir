# dark-factory — Sprint Factory Skill

A Cursor skill that takes a GitLab milestone and ships it: decompose, dispatch, integrate, deploy.

> *Huginn* — one of Odin's two ravens. He flies out, gathers information, comes back, and tells the chief what's going on. That's the Lead Engineer's job.

## What this is

A skill that runs a sprint as a dark-factory of specialist agents:

1. Reads the milestone, its issues, `docs/plans/**`, `docs/features/**`, and any referenced mockups
2. Produces a sprint plan and per-task blueprints
3. Decomposes into atomic tasks and spawns specialist workers in parallel via `tmux` + `fswatch`
4. Reviews worker output, rejects bad output, retries
5. Integrates merged MRs to `main` (or your integration branch)
6. Tags semver, pushes `release/x.y.z`, CI deploys staging; human reviews and promotes production manually

Everything runs on one machine with `git`, `glab`, `fswatch`, `tmux`, and `cursor-agent`. The factory runs **dark** — no mid-flight waits for human input; the LE writes `factory/RESULT.md` when staging is ready.

## Installation

This skill lives at `~/.cursor/skills/dark-factory/`. In Cursor, add that folder as a project or personal skill (attach the directory containing `SKILL.md`).

Required tooling:

```bash
brew install git glab fswatch tmux jq ripgrep fd
pip install playwright && playwright install chromium   # for manual-tester role
```

Plus `cursor-agent` (or `cursor`) on PATH.

## Adapt to a new project

The skill ships generic templates. Before running against a real repo, customize:

1. **`prompts/feature-builder.md` — Stack section:** replace "your project's architecture doc", test command, and MR tool with your actual values (e.g. `docs/architecture/SAO.md`, `.venv/bin/python -m pytest`, `glab`).

2. **`prompts/release-engineer.md` — Staging/promote section:** fill in the `<!-- customize -->` markers with your actual staging deploy command and production promote command.

3. **`prompts/lead-engineer.md`:** if your project has a cautious-developer quality bar doc, update the check 7 path. If it has Huginn-specific docs (`SAO.md`, BPE workflows), verify those paths exist in your repo or remove the references.

4. **`templates/task.md` — Checkpoint command:** replace the example test command with your project's equivalent.

5. **`templates/blueprint.md` — Issue URL:** replace the placeholder with your project's GitLab/GitHub URL pattern.

6. **Repo scripts (copy + wire once):** the skill ships process docs and prompts; the following scripts must exist in the target repo's `scripts/` directory — copy from an existing dark-factory repo or scaffold from scratch: `preflight.sh`, `claim.sh`, `done.sh`, `reject.sh`, `status.sh`, `bb-append.sh`, `verify-result.sh`, `integrate.sh`, `release.sh`, `archive.sh`.

## How to invoke

In a Cursor session inside a repo that has a GitLab milestone with Gherkin feature files, say:

- "Run the sprint on milestone M-2026-Q2-auth"
- "Ship the chat-agent sprint"
- "Kick off the factory for M-2026-Q2-auth"

The Lead Engineer agent will run `scripts/preflight.sh`, ingest all docs, decompose into tasks, spawn workers, integrate, and drive to staging — writing `factory/RESULT.md` when done.

## Skill layout

```
dark-factory/
├── SKILL.md                     # process contract + phases; read first
├── README.md                    # this file
├── agents/
│   └── dr-dobbs-v2.md           # cautious-developer quality bar (generic)
├── prompts/
│   ├── lead-engineer.md         # LE system prompt
│   ├── feature-builder.md       # worker prompt (generic — customize Stack section)
│   ├── step-def-writer.md       # worker prompt (generic)
│   ├── release-engineer.md      # worker prompt (customize staging/promote section)
│   └── manual-tester.md         # worker prompt (Playwright CLI mini-skill)
├── references/
│   ├── loop.md                  # LE event loop detail (Phase 3)
│   └── worker-protocol.md       # how workers claim, work, and report
├── scripts/
│   └── factory.sh               # tmux + worker spawner (bootstrap template)
└── templates/
    ├── task.md                  # task file shape
    ├── blueprint.md             # blueprint shape
    └── blackboard.md            # blackboard shape
```

Scripts that belong in the **target repo** (not shipped here): `preflight.sh`, `claim.sh`, `done.sh`, `reject.sh`, `status.sh`, `bb-append.sh`, `verify-result.sh`, `integrate.sh`, `release.sh`, `archive.sh`.

## Design notes

- **Filesystem-as-queue.** Atomic `mv` is faster, simpler, and more debuggable than any message broker for a single-machine factory. `fswatch` is one binary, no daemon.
- **Workers don't talk to each other.** All cross-task coordination goes through the LE. This avoids cascading context pollution.
- **The LE runs dark.** No blocking checkpoints — the LE logs decisions to `factory/blackboard.md` and proceeds. The human reads `factory/RESULT.md` when staging is ready.
- **Git as audit log.** Every task transition is one commit. `git log factory/` reads as the sprint's complete history.
- **Reject often.** Plan for ~1 rejection per task on average. The factory's value is parallel output + strict review, not perfect first-attempt output.
