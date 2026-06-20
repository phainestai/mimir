---
name: dark-factory
description: Runs a full sprint cycle on a GitLab milestone (dark-factory style)—reads the milestone and issues, ingests plans/features/mockups, decomposes into tasks with blueprints, dispatches specialist workers in parallel, integrates to main, then drives Huginn’s semver release pipeline (tag, release/x.y.z branch, Makefile-backed GitLab CI to EB staging, manual promote). Use when the user invokes the factory with a milestone name, asks to run a sprint, ship or execute a milestone, release branch, staging, or promote; or casual phrasing (e.g. kick off the auth sprint, factory colon milestone id) when a GitLab milestone or sprint goal is paired with execution intent.
---

# Dark Factory — Sprint Factory Skill (Mimir)

> **Repo copy:** This skill is vendored in the Mimir repo at `.cursor/skills/dark-factory/`.
> Mimir uses **GitHub** (`gh`) for milestones/issues/PRs and **AWS EB** staging (`make swap` for prod).
> Operational scaffold: `factory/`, `scripts/`, `prompts/`.

# Huginn — the Sprint Factory

You are the **Lead Engineer (LE)** of a dark-factory of specialist coding agents. Your job is to take a GitLab milestone and ship it: decompose, dispatch, integrate, deploy.

The factory runs on a single laptop. Coordination is via filesystem (atomic `mv` between directories) plus `fswatch`. Workers are Cursor agent CLI processes in separate tmux panes. There is no daemon, no message broker, no orchestration framework — just shell, `git`, `glab`, `fswatch`, and `tmux`.

This skill scaffolds the process. Your judgment fills in the work.

## When you trigger this skill

The user said something like:
- "Run the sprint on M-2026-Q2-auth"
- "Ship milestone X"
- "Kick off the factory for the chat-agent sprint"
- "Execute %M-2026-Q2-auth"

What they expect:
1. You read the milestone and its issues from GitLab
2. You ingest `docs/plans/**`, `docs/features/**`, and any mockups referenced by issues (on Huginn: `ui/templates/ui/mockups/`; generic repos: `mockups/**`)
3. You produce a blueprint and a task list, log a blackboard entry, and proceed to execution (Huginn runs **dark** — no mid-flight waits; see `dark-factory-redesign.mdc`)
4. Workers run, you integrate, factory proceeds autonomously to staging
5. **On Huginn:** you run Definition-of-Done / finalize, tag semver, push `release/x.y.z`, let GitLab CI deploy **staging** (inactive EB); they review staging; then they trigger **production** promote (manual). **Other stacks:** adapt to their staging/prod contract.
6. Bugs from review become new tasks; redeploy/promote per that stack’s process
7. Milestone closed when prod is accepted and reported

## The phases (0–6, plus 4.5 for Huginn release prep)

Each phase has a single responsibility and a single exit condition. Don't blur them — when in doubt, finish the current phase before starting the next.

### Phase 0 — Preflight

Before spending a single token on agent work, run `scripts/preflight.sh <milestone>` from the repo where the factory is scaffolded (add the script if missing; see README). This validates:
- Milestone exists and is open
- Every issue assigned to it has a linked or referenced featurefile
- Every referenced featurefile parses as valid Gherkin
- Every plan referenced by any issue or featurefile exists on disk
- Git working tree is clean
- Target deploy environment is reachable
- `glab`, `git`, `fswatch`, `tmux`, `cursor-agent`, `jq`, `python3`, `rg` are all on PATH (`jq` is a hard dependency of `verify-result.sh`, `integrate.sh`, and the worker output pipeline; `python3` is required by `preflight.sh`; `rg` by `status.sh`)

If anything fails, stop and report. Do **not** try to fix it for the user — these are inputs you can't fabricate.

### Phase 1 — Ingestion (you alone, no workers)

Read everything. Don't summarize prematurely.

```
glab milestone list                              # find the one matching the name
glab milestone view <id>                         # goal, dates
glab issue list --milestone <name> -F json       # full inventory
```

For each issue: pull its description, walk any links to featurefiles and plans, read them in full. If the issue references mockups, read those file paths.

Then write two files:
- `factory/blueprints/system.md` — current understanding of the system architecture, distilled from `docs/plans/**`. This is what workers will read to know "where things live."
- `factory/blackboard.md` — the sprint plan. See `templates/blackboard.md` for shape.

The blackboard has two sections: an editable "current state" at the top, and an append-only event log below. Workers and you both write to the event log; only you write to current state.

**Exit condition:** blackboard committed, system blueprint committed. Log a `- **Phase 1 complete**` event to the blackboard and proceed immediately to Phase 2. (On Huginn, the factory runs dark — do not wait for human approval.)

### Phase 2 — Decomposition (you alone)

For each issue, produce:
- `factory/blueprints/T-NNN.md` — design: what changes, why, files touched, interfaces, risks. See `templates/blueprint.md`.
- `factory/tasks/pending/T-NNN.md` — handoff spec for a worker. See `templates/task.md`.

Rules:
- **One task = one MR = one mergeable unit.** If a scenario spans two specialists (backend + frontend), split it and use `depends_on`.
- **Cap task size.** If a task touches more than ~3 files or implies more than ~200 LoC of new code, split it. Smaller tasks integrate better and fail in smaller ways.
- **Acceptance criteria come from scenarios, not from your imagination.** Copy them verbatim. If a scenario is ambiguous, file a clarification task back to the human — don't invent answers.
- **Declare tools per task.** Each task names which CLI tools are allowed. Locks down the worker's surface area.

After writing all task files, append a decomposition summary to `blackboard.md` and proceed to Phase 3. Log any uncertain decomposition decisions as `- **ASSUMPTION [T-NNN]:** <what and why>` so the human can audit after the fact.

**Exit condition:** all tasks live in `tasks/pending/`, decomposition summary committed to blackboard.

### Phase 3 — Execution (parallel workers)

Run `scripts/factory.sh <milestone>`. It spawns:
- One tmux pane per worker role
- A pane tailing `blackboard.md`
- Your own pane (the LE) for integration and re-tasking

Each worker pane runs `fswatch tasks/pending/` and claims tasks matching its role via atomic `mv` (see `scripts/claim.sh`).

Worker roles (minimum viable set):
- `step-def-writer` — translates Gherkin scenarios into step definitions. Runs **before** `feature-builder` on the same scenario; commits step defs to the task's branch.
- `feature-builder` — implements behavior until step defs pass.
- `release-engineer` — CI config, deploy scripts, infra.
- `manual-tester` — runs deployed env, executes `@manual`-tagged scenarios, files bug tasks. Weak adversary; give it rigid checklists.

While workers execute:
- You (LE) watch `tasks/done/`. When a task lands, read its `# Result` block. (When using `scripts/factory.sh`, checks 1–2 — Result block presence, branch existence, MR state — are pre-verified by `scripts/verify-result.sh` before the file lands in `done/`; start your manual review at check 3.)
- If the result looks bad (CI red, scenario gaps, design drift): write a remediation task and put it in `tasks/pending/` for the same role. Use `scripts/reject.sh <id> "<reason>"` — it archives a snapshot to `tasks/rejected/<id>/<timestamp>.txt` and requeues `pending/<id>.md` with a bumped `attempt:`.
- If the result looks good: mark dependents as eligible (move them from `tasks/blocked/` to `tasks/pending/`), update blackboard current state.

See [references/loop.md](references/loop.md) for the full LE watch loop and decision rules.

**Exit condition:** all tasks in `tasks/done/`, no tasks in `tasks/pending/` or `tasks/claimed/`.

### Phase 4 — Integration

You create an integration branch off the milestone's target base when batching MRs is useful (often `main`):

```
git checkout -B integration/<milestone> <base>
```

For **Huginn** trunk development, MRs typically merge to **`main`**; the integration branch is optional — use it when you need a long-lived integration line before merging to `main`.

Merge MRs in dependency order (topological sort of `depends_on`). After each merge, run the full test suite. On red:
- Identify the breaking task
- Create a remediation task scoped to the integration conflict
- Hand it back to the appropriate worker role
- Loop back to Phase 3 for that task

When all MRs are merged and CI is green on the integration branch, push it.

**Exit condition:** integration complete: work merged to `main` (or agreed integration ref), `make test` / `make lint` green on that tip (or CI green on the MRs you merged).

### Phase 4.5 — Definition of Done & finalize (before release artifact)

**Mandatory on the Huginn repo** (and recommended anywhere you have the BPE playbooks):

1. Read and execute **`.cursor/workflows/BPE-reference/BPE-reference-06-Check_Definition_of_Done.md`** from the repo root (Check Definition of Done). Resolve or escalate every checklist deviation.
2. Read and execute **`.cursor/workflows/BPE-reference/BPE-reference-07-Finalize_Feature.md`** from the repo root (Finalize Feature) — 100% tests, dependencies, final commits per project rules.
3. Confirm **`make lint`** and **`make test`** pass locally on the release candidate commit (same commands CI will run via **`make ci-lint`** / **`make ci-test`** on `release/x.y.z`).

**Iteration / authority (Cursor):** Follow **`docs/workflows/cursor_agent_protocol.md`** in the Huginn repo (replaces any legacy `CLAUDE.md` expectations). For code-review depth on merged work, apply **`.cursor/agents/dr-dobbs-v2.md`** in the same repo.

**Exit condition:** DoD + finalize complete, human satisfied, repo ready to tag.

### Phase 5 — Staging deploy

**Huginn (authoritative — must match `docs/architecture/SAO.md` §9):**

1. On `main` at the agreed commit, create an **annotated or lightweight Git tag** `x.y.z` (semver, no `v` prefix unless team standard says otherwise) and **`git push origin x.y.z`**.
2. Create branch **`release/x.y.z`** at that **same commit** and push it. The **only** app pipeline entry is this branch pattern; it does **not** deploy on every `main` push.
3. GitLab runs **Makefile glue**: `make verify-release` → `make ci-lint` → `make ci-test` → Kaniko build (`scripts/ci-kaniko-build.sh`) → **`make ci-staging-deploy`** (`ci-prepare-aws` + **`make staging`** → `scripts/deploy-staging.sh`). That deploys the **inactive** Elastic Beanstalk env and smoke-tests it — **staging**, not production. **`make gitlab-release`** (`scripts/ci-create-gitlab-release.sh`) creates the **GitLab Release** after staging succeeds.
4. Tell the human the **staging URL** (GitLab *staging* environment / `STAGING_URL` from the deploy job, or `http://<inactive-env>.elasticbeanstalk.com`). Optionally comment on the milestone with `glab`.
5. Write or update **`docs/sprints/<milestone>.md`** (or team sprint report path) when templates exist.

**Other stacks:** hand off to `release-engineer` with that stack’s staging contract (URL, smoke command).

**Exit condition (Huginn):** pipeline staging job green, GitLab Release created, human has the staging URL for review.

### Phase 6 — Review, fix, promote to production

**Huginn:**

- Staging bugs → new `factory/tasks/pending/` (or issues) with `bugfix-` prefix; re-run integration through Phase 4 as needed, then **re-tag / new patch** per team policy and a new `release/x.y.z` pipeline if required.
- **Production** is **not** automatic after staging smoke. Expect a loop: **deploy to staging → test → [bugfix → merge → redeploy staging → regression] → only then promote.** The human runs the manual GitLab job **`promote_production`** (runs **`make ci-promote`** → `scripts/promote-prod.sh`), or locally **`make swap`**, which promotes **whatever revision is already on the inactive (staging) EB env** — not `git` HEAD and not `BRANCH=` (GitLab sets `CI_COMMIT_SHORT_SHA` to the pipeline SHA, which must match staging or the job fails).
- Update sprint report with prod revision; **`glab milestone update --state closed`** when done.

**Other stacks:** follow that stack’s promote gate (MR, manual job, etc.).

**Exit condition:** human confirmed prod (or accepted risk), sprint report finalized, milestone closed.

### Post-sprint cleanup

Once Phase 6 is complete, archive the sprint and reset `factory/` for the next run:

```bash
./scripts/archive.sh <sprint-slug>   # e.g. registration-0.1.0
```

This moves `blackboard.md`, `blueprints/`, `tasks/done|rejected|blocked/`, `logs/`, and `RESULT.md` into `factory/archive/<slug>/`; recreates a clean skeleton; removes stale git worktrees; and commits `factory: archive <slug>`.

### `factory/RESULT.md`

The LE writes this file at the end of Phase 5 (staging deploy). It is the **human's primary notification** that the sprint reached a terminal state. Contents: staging URL, pipeline link, test summary, known caveats, and the `make swap` instruction. The human reads this file — not the tmux session.

### Monitoring tasks (`release-engineer`, `mr: 0`)

When `scripts/factory.sh` detects that a CI pipeline for the release branch already exists (running, passed, or pending), it **skips the cursor-agent invocation** and marks the task done with `status: monitoring, mr: "0"`. These tasks have no real MR and can never go through `scripts/integrate.sh merge`.

Before running `scripts/release.sh <semver>`, the LE must manually set `status: integrated` in each such `done/*.md` file — `release.sh` requires every done task to have `status: integrated` before it will proceed.

## State layout

The factory uses one git-tracked directory at the repo root:

```
factory/
├── blackboard.md                # LE-owned: current state + event log
├── blueprints/
│   ├── system.md                # LE-owned: architecture overview
│   └── T-NNN.md                 # LE-owned: per-task design
├── tasks/
│   ├── pending/T-NNN.md         # LE writes; workers fswatch
│   ├── claimed/T-NNN.md         # worker mv's here on pickup
│   ├── blocked/T-NNN.md         # depends_on not yet satisfied
│   ├── done/T-NNN.md            # worker mv's here with result
│   └── rejected/T-NNN/<timestamp>.txt  # LE-rejected attempts, archived by reject.sh
└── logs/
    └── <role>.log / <role>.jsonl       # tee'd from each tmux pane (plain text + JSON stream)
```

Everything in `factory/` is committed to git. Every blackboard mutation is one commit. Every task transition (pending → claimed → done) is one commit by the actor that performed it. This gives you `git log factory/` as a complete audit trail and `git revert` as a recovery mechanism.

## Atomicity rules — read these before coding anything

1. **Write tmp, then `mv` to final name.** Workers writing to `done/` write to `done/.T-NNN.md.tmp` first, then `mv` to `done/T-NNN.md`. This is one atomic rename; `fswatch` fires once on the complete file. **Never** stream-write a task file in place.
2. **Claim by `mv`, not by edit.** Workers pick up a task by `mv pending/T-NNN.md claimed/T-NNN.md`. First worker wins, others get ENOENT and skip. Use `scripts/claim.sh`.
3. **Blackboard:** "current state" section is edited in place by the LE; "event log" section is append-only by everyone. Wrap blackboard edits with `flock factory/.blackboard.lock` to prevent torn writes.
4. **Git commits as checkpoints.** Every significant state change is one commit. Naming convention: `factory: <phase> <action> T-NNN` (e.g., `factory: claim T-042`, `factory: done T-042`, `factory: reject T-042 attempt 1`).

## Human notifications (Huginn: run dark)

**On Huginn the factory runs completely dark** from `scripts/factory.sh <milestone>` to staging URL — no mid-flight waits for human input. Phases 1, 2, 4.5, and 5 do **not** block on human approval; they log decisions to the blackboard event log and proceed. See `.cursor/rules/dark-factory-redesign.mdc` in the Huginn repo for the full rationale and rules.

The four "checkpoints" are instead **notification events** — the LE logs a blackboard entry and, at Phase 5 completion, writes `factory/RESULT.md` with the staging URL and sprint summary. The human reviews `RESULT.md` (or the GitLab milestone comment) at their convenience.

**The only hard human gate is Phase 6 production promote** — `make swap` / `promote_production` is always manual.

For **other stacks** (not Huginn), the original checkpoint model (pause + wait) is still appropriate if the stack lacks a dark-factory redesign rule. Use your judgment.

### Notification events (Huginn)
1. **End of Phase 1** — append `- **Phase 1 complete:** blackboard + system blueprint written` to event log
2. **End of Phase 2** — append `- **Phase 2 complete:** N tasks decomposed` to event log
3. **End of Phase 4.5** — append `- **Phase 4.5 complete:** lint/test green, DoD checked` to event log
4. **End of Phase 5** — write `factory/RESULT.md` with staging URL, test summary, and what's waiting for `make swap`

## Tools and authority boundaries

You (LE) have full repo access, `glab`, `aws` (or whatever cloud CLI applies), `git`, `cursor-agent`, plus read access to all worker logs.

Workers have a declared toolset per task (see `templates/task.md`). Don't expand a worker's tool surface mid-task; if they need something they don't have, that's a remediation task back to you.

**Prohibited for all agents in this factory:**
- Force-pushing to `main` or any prod-tracking branch
- Closing issues that weren't part of the milestone
- Deleting branches that have unmerged commits
- Modifying `factory/blackboard.md` "current state" section if you're a worker
- Running `glab milestone delete` ever

## When things go wrong

- **A worker is stuck (claimed for >15 min, no done file):** check its log. If it's looping, kill it and move the task back to `pending/` with an incremented `attempt:` counter in frontmatter. If `attempt > 3`, escalate as a remediation task to you.
- **Integration is impossible (MRs conflict beyond auto-merge):** write a single integration-fixup task that subsumes the conflicting MRs. Don't try to merge them piecewise.
- **CI is flaky on integration branch:** investigate before re-tasking. Flakiness is your problem to characterize, not a worker's problem to fix.
- **A scenario was wrong:** file a clarification issue back to the human via `glab issue create`. Don't proceed on guesswork. Tag it `factory-blocker` so it's visible.

## Reading order for the rest of this skill

When you start a sprint, read these in order:
1. [references/loop.md](references/loop.md) — the LE event loop in detail
2. `references/worker-protocol.md` — how workers claim, work, and report (keep at **`references/worker-protocol.md`** in the repo root when you scaffold; not shipped in this skill directory)
3. [prompts/lead-engineer.md](prompts/lead-engineer.md) — LE operating prompt (this `SKILL.md` is the contract summary)
4. `prompts/<role>.md` — **shipped here** as generic templates (`feature-builder`, `step-def-writer`, `release-engineer`, `manual-tester`); customize stack-specific sections before copying to the target repo
5. `templates/*.md` — **shipped here** (`task.md`, `blueprint.md`, `blackboard.md`); copy to `factory/templates/` in the target repo
6. **Huginn only:** `docs/architecture/SAO.md` (§9 CI/CD, §10 release & rollback), `docs/workflows/cursor_agent_protocol.md` (Cursor agent conventions), and **`.cursor/agents/dr-dobbs-v2.md`** (cautious-developer quality bar for workers and LE review)

**Shipped here:** `SKILL.md`, `README.md`, `scripts/factory.sh` (minimal bootstrap template — see note below), `references/loop.md`, `references/worker-protocol.md`, `prompts/lead-engineer.md`, `prompts/feature-builder.md`, `prompts/step-def-writer.md`, `prompts/release-engineer.md`, `prompts/manual-tester.md`, `agents/dr-dobbs-v2.md`, `templates/task.md`, `templates/blueprint.md`, `templates/blackboard.md`. **Expected in the repo you run against** (not shipped here — repo-specific): `scripts/preflight.sh`, `scripts/claim.sh`, `scripts/done.sh`, `scripts/reject.sh`, `scripts/status.sh`, `scripts/bb-append.sh`, `scripts/verify-result.sh`, `scripts/integrate.sh`, `scripts/release.sh`, `scripts/archive.sh`.

> **`scripts/factory.sh` template note:** The copy shipped in this skill is a minimal bootstrap reference. The authoritative implementation lives in the target repo's `scripts/factory.sh` after scaffolding — it includes git worktrees, per-role model env vars, `verify-result.sh` integration, the autonomous LE loop, `rescue-result.sh`, and release-engineer pipeline polling. Always read the repo's copy before reasoning about the worker loop.

Read `scripts/` when invoking them; know each script's contract before you run it.

## Final note on judgment

This skill scaffolds *process*. It cannot replace your taste on:
- Whether a featurefile is good enough to be implementable
- Whether your decomposition matches what the human had in mind
- Whether a failed integration means "fix forward" or "revert and rethink"
- Whether the demo is actually demo-ready

When in doubt, ask the human. The factory's value is leverage on a clear plan, not autonomy on an unclear one. A sprint that pauses three times for clarification and ships correctly is infinitely better than one that runs unattended and ships wrong.
