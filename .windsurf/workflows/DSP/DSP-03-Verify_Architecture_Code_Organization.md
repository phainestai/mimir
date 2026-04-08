# Activity: Verify Architecture & Code Organization

**Activity ID**: TBD
**Order**: 3
**Phase**: Prerequisite Check
**Dependencies**: Predecessor: DSP-02 (Verify DTA Artifacts)

## Description

Verify Architecture & Code Organization

## Guidance

# Verify Architecture & Code Organization

## Objective

Verify that the project has a defined code organization, technology stack, and working project structure. This goes beyond SAO.md existence (DSP-02) to check that the architectural decisions have been realized in the actual codebase or are clearly documented for a greenfield project.

---

## Process

### 1. Check Project Structure Exists

For an **existing project**, verify:

| Check | What to Look For | Source |
|-------|------------------|--------|
| **Project root** | `manage.py`, `package.json`, `Cargo.toml`, or equivalent entry point | DTA-04 |
| **Source directories** | Application code directories matching SAO.md structure | DTA-04 |
| **Test directories** | `tests/` or equivalent with at least one test file | DTA-06 |
| **Dependency file** | `requirements.txt`, `package.json`, `Cargo.toml`, etc. | DTA-04 |
| **CI/CD config** | `.github/workflows/`, `Jenkinsfile`, etc. (optional for greenfield) | DTA-10 |

For a **greenfield project** (no code yet), verify that SAO.md contains:
- Explicit directory layout plan (from DTA-04)
- Technology stack decisions (languages, frameworks, databases)
- These will be used by BSP (Bootstrap Project) workflow to create the structure

### 2. Check Workflow & Skill Coverage

Scan `.windsurf/workflows/` for available workflows:

```
Available Workflows:
  ESM  | Envision the System     | 7 activities  | ✅
  DTA  | Define Architecture     | 18 activities | ✅
  DSP  | Deploy Software Process | 6 activities  | ✅ (this workflow)
  BSP  | Bootstrap Project       | 8 activities  | ✅
  BPE  | Build Feature           | N activities  | ✅
  EST  | Estimate the Project    | 8 activities  | ✅
```

Scan for available skills (if any exist in workflow `skills/` directories):

```
Available Skills:
  BSP/skills/  | 3 skills found
  (others)     | ...
```

Scan for available artifact templates:

```
Available Artifact Templates:
  ESM/artifacts/  | user_journey_template.md, feature_file_template.feature, ...
  DTA/artifacts/  | sao_document_template.md
  DSP/artifacts/  | claude_md_template.md, copilot_instructions_template.md, ...
```

### 3. Evaluate Readiness

**Ready to proceed** if:
- SAO.md has technology stack and directory layout (from DSP-02)
- Either project structure exists OR SAO.md documents the planned structure
- At least BPE workflow is available (the AI needs to know how to build features)

**Not ready** if:
- No technology stack defined in SAO.md → redirect to **DTA-02** (Define Application Blocks)
- No directory layout in SAO.md → redirect to **DTA-04** (Define Code Organization)
- No BPE workflow available → this is a critical gap, inform user

### 4. Report Summary

```
Architecture & Code Organization Check:
  Technology stack defined   | ✅ Django 5 + SQLite + HTMX
  Directory layout defined   | ✅ In SAO.md Section "Project Structure"
  Project structure exists   | ✅ 4 Django apps, tests/, docs/
  BPE workflow available     | ✅ .windsurf/workflows/BPE/
  Skills available           | ✅ 3 skills in BSP/skills/
  Artifact templates         | ✅ 7 templates across workflows
```

---

## Deliverables

- ✅ **Project structure** verified or planned
- ✅ **Workflow coverage** inventoried
- ✅ **Skill coverage** inventoried
- ✅ **Artifact template coverage** inventoried
- ✅ **All prerequisites met** — or user redirected to specific DTA/ESM activities
- ✅ **Ready to proceed** to DSP-04

## Artifacts Produced

- Architecture & code organization verification report
- Inventory of available workflows, skills, and artifact templates (input for DSP-05)

## Artifacts Consumed

- `docs/architecture/SAO.md` (sections on tech stack, directory layout)
- `.windsurf/workflows/*/` directory listing
- `.windsurf/workflows/*/skills/` directory listing
- `.windsurf/workflows/*/artifacts/` directory listing
- Project root directory listing

## Notes

This activity serves double duty: (1) it gates the workflow to ensure we have enough architectural context to generate a useful AI config, and (2) it inventories all available workflows, skills, and artifact templates — which DSP-05 will reference in the generated config file.
