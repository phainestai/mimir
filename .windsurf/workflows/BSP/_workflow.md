# Bootstrap Project

**Playbook**: FeatureFactory v3.8 (Draft)
**Workflow ID**: TBD
**Description**: Bootstrap a greenfield project from SAO.md and MODUS_OPERANDI.md decisions. Install prerequisites, initialize repository, scaffold structure, configure tooling, create Makefile, and verify with a welcome page. Make-centric, *nix-oriented, idempotent.
**Phase Organization**: Uses phases (Provision → Initialize → Configure → Verify)
**Total Activities**: 7
**Export Date**: 2026-04-06

## Prerequisites

- Completed DTA workflow → `docs/architecture/SAO.md` (with Technology Stack Table)
- Completed DSP workflow → `docs/process/MODUS_OPERANDI.md`
- macOS with Homebrew or Linux with apt/dnf

## Output

- Git repository with project structure per DTA-04
- All dependencies installed via `make provision`
- F5 (or `make run`) → welcome page showing app health
- All Makefile targets functional: `provision`, `run`, `test`, `lint`, `format`, `clean`, `help`

## Activities

See individual activity files in this directory.

## Editing Instructions

- **Add activity**: Create new file with pattern BSP-XX-Name.md
- **Remove activity**: Delete the .md file
- **Reorder**: Rename files to change order numbers
- **Edit content**: Modify description, guidance, dependencies
- **Change phase**: Update the Phase field

After editing, use import_workflow_from_local MCP tool to import changes.
