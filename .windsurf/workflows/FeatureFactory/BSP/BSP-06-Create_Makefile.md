# Activity: Create Makefile

**Activity ID**: 93
**Order**: 6
**Phase**: Elaboration
**Dependencies**: None

## Description

Create Makefile

## Guidance

# Create Makefile

## Objective

Create a comprehensive Makefile that serves as the **single orchestration layer** for all development, infrastructure, and deployment operations. CI/CD pipelines call these targets — no business logic lives in GitHub Actions.

The Makefile template is in `BSP/artifacts/makefile_template.mk`. Copy it, adapt variables to your stack, and verify all targets work.

---

## Process

### 1. Copy Makefile Template

Copy `BSP/artifacts/makefile_template.mk` to your project root as `Makefile`.

The template includes:
- **Base sections**: General, Provision, Development, Testing, Code Quality, Database, Cleanup
- **Extension points**: `##@ Infrastructure` and `##@ Deployment` sections (commented out, added by DCI/DCD workflows later)
- **Commented variable blocks** for infra and deployment (uncommented during DCI/DCD)

See the full template: [`BSP/artifacts/makefile_template.mk`](artifacts/makefile_template.mk)

### 2. Adapt to Stack

- Read SAO.md Technology Stack Table for tool paths and versions
- If no Node.js in stack: remove `_npm-install` and `package.json` check
- If no Django: replace `manage.py` commands with framework equivalents
- If additional tools (e.g., Docker): add `docker-up`, `docker-down` targets
- All targets should follow the pattern: verb-noun (e.g., `test-unit`, `db-init`)
- **Do NOT uncomment** `##@ Infrastructure` or `##@ Deployment` sections yet — those are added by DCI and DCD workflows respectively

### 3. Verify All Targets

Run each target and verify it works:
```bash
make help        # Should show formatted help
make provision   # Should complete without errors
make lint        # Should run (may report issues — that's OK)
make format      # Should run
make test        # Should run (may have 0 tests — that's OK)
make clean       # Should clean up
```

### 4. Commit Makefile

```bash
git add Makefile
git commit -m "chore(make): create Makefile with provision, run, test, lint, format, clean targets"
```

---

## Deliverables

- ✅ **Makefile** created with all standard targets
- ✅ **`make help`** shows all targets with descriptions
- ✅ **`make provision`** installs everything from scratch
- ✅ **All targets** verified as functional
- ✅ **Makefile committed**

## Agent

None

## Skill

None

## Rules

None

## Artifacts Produced

- **Makefile Template** (Code) - Required

## Artifacts Consumed

None

## Notes

No additional notes.
