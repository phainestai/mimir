# ITER-20260501 — Complete Versioning for the Playbooks

## Outcome

Milestone **#6** delivered **S01–S15** on branch `iteration/20260501-versioning-complete`: Decimal X.Y `PlaybookVersion` schema, legacy backfill migration, release and re-release with required descriptions, PIP apply with a single +0.1 minor per batch, staff revert Released→Draft, and History UI (listing, snapshot, compare, PIP markers).

## What worked

- Serial MIT loop with explicit GitHub checkpoints kept scope traceable per issue.
- Centralizing version bumps in `PlaybookService` and `pip_apply_service` avoided duplicate signal-driven increments on released playbooks.

## Risks / follow-ups

- Admin revert adds a `PlaybookVersion` row only when no row exists for the current `(playbook, version_number)` (unique constraint).
- Global `pytest` assumes draft workflow signals account for pre-release version when asserting “first major” lines.

## References

- Milestone **#6**, issues **#83–#97**.
