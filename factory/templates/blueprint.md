# Blueprint: T-NNN — <short title>

**Issue:** [#NNN](<!-- your-project-issue-url/-/issues/NNN -->)
**Task:** [`factory/tasks/pending/T-NNN.md`](../tasks/pending/T-NNN.md)

## Goal

One paragraph: what capability is being added or changed, and why.

## Context

What the LE understands about the current state of the system that is relevant to this
task. Include: where the entry point is, which template/view/model is involved, any
existing patterns the worker should follow.

Point workers at the exact files they need to read first:
- `path/to/existing/file.py` — why it matters
- `docs/features/area/scenario.feature` — the acceptance contract

## Files touched

| File | Change |
|------|--------|
| `path/to/file.py` | create / modify / delete |

## Interfaces changed

Describe any new URLs, function signatures, DB columns, template context variables, or
JS hooks this task introduces. Be precise — dependent tasks will be written against this
interface description.

## Risks

- What could go wrong?
- Any ambiguity in the featurefile that the worker should flag rather than guess?
- Any migration / data concern?

## Acceptance

Restate the Gherkin scenario title(s) from the task, plus what "green" looks like:

- `<your test command> -k "<scenario>" --tb=short` exits 0
- No regressions: full test suite still green
- Lint clean
