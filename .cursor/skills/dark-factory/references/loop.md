# The Lead Engineer event loop

During Phase 3 (Execution), you (LE) are not just sitting waiting. You actively watch the factory and react to what workers produce. This document is the protocol for that.

## What you watch

In your tmux pane, run:

```
fswatch factory/tasks/done factory/tasks/rejected factory/tasks/blocked
```

(Workers watch `tasks/pending/` themselves. The LE does not need to watch it — workers claim tasks autonomously. The LE wakes on `done/` for review, `rejected/` to track rejection cycles, and `blocked/` to unblock dependency-satisfied tasks.)

This fires on any state transition. For each fired path:

1. If a file appeared in `factory/tasks/done/`: **review work** (next section).
2. If `factory/tasks/pending/` is empty AND `factory/tasks/claimed/` is empty AND `factory/tasks/blocked/` is empty: **Phase 3 is complete**, transition to Phase 4.
3. If a file appeared in `factory/tasks/blocked/` and its `depends_on` are now all in done: move it back to `pending/`. Workers will pick it up.
4. If a worker pane has been silent for >15 minutes while a task is in `claimed/`: investigate (see "stuck worker" below).

## Reviewing a done task

When `factory/tasks/done/T-NNN.md` appears, run these checks in order. Stop at the first failure and reject.

> **When using `scripts/factory.sh`:** checks 1–2 below (Result block presence, non-empty fields, branch existence, MR state `opened` or `merged`) are pre-verified by `scripts/verify-result.sh` before the file ever lands in `done/`. A task that fails those checks goes to `tasks/blocked/` instead. You can therefore start your manual review at check 3 (CI status) for any task that reached `done/`.

### 1. Worker honesty

- File exists and has both the original task content **and** a `# Result` block
- `status:` is one of `passed`, `failed`, `blocked`
- If `status: failed` or `status: blocked`: don't run the rest of the checks. Read the worker's notes and decide: re-queue with more guidance, or escalate to the human.

### 2. Branch and MR exist

- `git ls-remote origin <branch-from-result>` returns a SHA matching `commit_sha`
- `glab mr view <mr-from-result>` returns an open MR (or merged if it's a fast-mover)
- MR description contains `Closes #<issue>` (or whatever your project's closing keyword is)

### 3. CI status

- `glab mr view <mr> -F json | jq -r '.head_pipeline.status'` returns `success`
- If pending: wait up to 10 minutes, then re-check. If still pending, log and continue (CI delay is not a worker fault).
- If failed: quote the failing job name and the relevant log lines in the rejection reason.

### 4. Scope

- `git diff origin/<base>...origin/<branch> --name-only` produces a list of changed files
- Every file must be in the task's "Files in scope" section OR in `out_of_scope_changes:` with a written justification
- If a file was changed without justification: reject.

### 5. Acceptance criteria

- Each scenario named in the task must be green. For BDD projects, run the test suite filtered to those scenarios on the branch and check exit code.
- The full test suite on the branch must be green (no regressions).
- For a step-def-writer task: instead of scenarios being green, check that they're now defined (not "step undefined") and red (not vacuously green).

### 6. Smoke

For tasks that imply runtime behavior (most feature-builder tasks), run the scenario end-to-end against a local instance of the branch. This catches "tests are green but the feature is broken" — which happens more than it should.

## Writing a rejection

Use `scripts/reject.sh <task-id> "<reason>"`. The reason should:

- Name the specific check that failed (1–6 above)
- Quote the evidence (failing scenario name, file outside scope, CI job)
- State what "fixed" looks like in one sentence

Bad rejection: "tests are failing, please fix"
Good rejection: "Check 5 failed. Scenario 'magic link sent within 5s' in `docs/features/auth/magic-link.feature` is red on attempt 1. Local run shows the email is sent but takes 8s. Expected: sub-5s. Likely cause: synchronous SMTP call; consider queueing."

## Stuck workers

A worker pane that's silent for >15 minutes with a task in `claimed/`:

1. Look at the worker's log: `tail -100 factory/logs/<role>.log`
2. If the worker is looping (same actions repeated, no progress): the model is stuck. Kill the cursor-agent process in that pane, move the task back to `pending/` with `attempt:` incremented.
3. If the worker is doing useful work but slowly: leave it alone. Long tasks are fine; loops are not.
4. If the worker has died (no process): re-spawn that worker pane and move the task back to `pending/`.

## When to spawn a remediation task vs re-queue the original

- **Re-queue (increment `attempt:`):** the task as described is still the right task; the worker just did it wrong. Add a "Prior attempt feedback" section pointing at what went wrong.
- **Remediation task (new T-NNN):** the original task is fine to leave done (or at least archive), but additional work is needed that wasn't anticipated. Example: integration revealed a contract mismatch that's nobody's fault.

If you find yourself escalating the same task to attempt 3, **stop and read the blueprint again.** Likely the blueprint is the problem, not the worker. Rewrite the blueprint, then re-queue with attempt reset to 1 and a note that the blueprint changed.

## Integration trigger

When all tasks in a connected dependency cluster are done (i.e., no task in the cluster is pending, claimed, or blocked), you can integrate that cluster without waiting for unrelated clusters. This is the main parallelism win — don't serialize integration if you don't have to.

The simplest heuristic: a "cluster" is a connected component in the `depends_on` graph. Integrate each component as soon as it completes.

## Phase 3 exit

You leave Phase 3 when:
- `factory/tasks/pending/` is empty
- `factory/tasks/claimed/` is empty
- `factory/tasks/blocked/` is empty
- All tasks are in `factory/tasks/done/` (or terminally `rejected/` with human escalation logged)

To confirm these conditions, either poll `scripts/status.sh` (prints pending/claimed/done/blocked counts) or check directories directly:

```bash
ls factory/tasks/pending/ factory/tasks/claimed/ factory/tasks/blocked/
# all should be empty (or contain only .gitkeep)
```

Append a Phase 3 exit event to the blackboard and transition to Phase 4.
