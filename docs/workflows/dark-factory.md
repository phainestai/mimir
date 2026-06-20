# Dark Factory (Mimir)

This repo vendors the **dark-factory** sprint factory skill and operational scaffold.

## Quick start

1. Read [.cursor/skills/dark-factory/SKILL.md](.cursor/skills/dark-factory/SKILL.md) — full process contract.
2. Read [factory/README.md](factory/README.md) — commands and layout.
3. Preflight: `./scripts/preflight.sh 'Milestone Title'`
4. After LE fills `factory/tasks/pending/`: `./scripts/factory.sh 'milestone-slug'`

## Layout

| Path | Purpose |
|------|---------|
| `.cursor/skills/dark-factory/` | Cursor skill (attach or auto-discover) |
| `factory/` | Blackboard, blueprints, task queue |
| `prompts/` | Worker + LE prompts (`factory.sh` reads these) |
| `scripts/` | `preflight`, `factory`, `integrate`, `release`, … |
| `references/worker-protocol.md` | Claim / Result / PR protocol |
| `agents/dr-dobbs-v2.md` | Worker quality bar |

## Prerequisites

Everything installable is covered by **`make provision`** (Python + factory CLIs).

```bash
make factory-check   # optional strict re-check (gh auth + cursor-agent)
```

After first provision, complete manually if prompted: `gh auth login`, Cursor CLI (`cursor-agent`).

## Mimir specifics

- **Tracker:** GitHub milestones + issues (`gh`, not `glab`)
- **Staging:** GitHub Release `vX.Y.Z` → CI → idle EB (`mimir-idle`)
- **Production:** `make swap` (manual)

## Related

- FeatureFactory iteration (PIT/MIN): `.cursor/rules/iteration-protocol.mdc`
- Architecture: `docs/architecture/SAO.md`
