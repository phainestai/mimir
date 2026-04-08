# Deploy Software Process

**Playbook**: FeatureFactory v3.8 (Draft)
**Workflow ID**: TBD
**Description**: Check prerequisite artifacts (ESM, DTA), choose target AI IDE, and generate configuration (CLAUDE.md / copilot-instructions.md / Windsurf rules) so AI can consume docs/**, workflows, skills, and artifact templates to start building features.
**Phase Organization**: Uses phases (Prerequisite Check → Configuration → Finalization)
**Total Activities**: 6
**Export Date**: 2026-04-08

## Prerequisites

- Completed ESM workflow → user journey, screen flows, feature files, IA guidelines
- Completed DTA workflow → `docs/architecture/SAO.md`

## Output

- AI IDE configuration file for chosen target:
  - **Claude Code** → `CLAUDE.md`
  - **GitHub Copilot** → `.github/copilot-instructions.md`
  - **Windsurf/Cursor** → `.windsurf/rules/` + `.cursor/rules/`

## Activities

See individual activity files in this directory.

## Editing Instructions

- **Add activity**: Create new file with pattern DSP-XX-Name.md
- **Remove activity**: Delete the .md file
- **Reorder**: Rename files to change order numbers
- **Edit content**: Modify description, guidance, dependencies
- **Change phase**: Update the Phase field

After editing, use import_workflow_from_local MCP tool to import changes.
