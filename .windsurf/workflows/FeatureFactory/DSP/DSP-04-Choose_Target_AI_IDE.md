# Activity: Choose Target AI IDE

**Activity ID**: 63
**Order**: 4
**Phase**: Inception
**Dependencies**: None

## Description

Choose Target AI IDE

## Guidance

# Choose Target AI IDE

## Objective

Ask the user which AI-assisted IDE they will use for development, then record the choice to determine the output format for DSP-05 (Generate AI IDE Configuration).

---

## Process

### 1. Present Options

Ask the user to choose their primary AI IDE:

| Target | Output File(s) | Format |
|--------|----------------|--------|
| **Claude Code** | `CLAUDE.md` at project root | Single Markdown file with all context |
| **GitHub Copilot** | `.github/copilot-instructions.md` | Single Markdown file in `.github/` |
| **Windsurf** | `.windsurf/rules/*.md` files | Multiple rule files + workflow references |
| **Cursor** | `.cursor/rules/*.mdc` files | Multiple rule files in MDC format |

### 2. Clarify Multi-IDE Usage

If the user works with multiple IDEs (e.g., Windsurf for daily work + Claude Code for complex tasks):

- Generate configs for **all selected targets**
- Ensure consistency across configs (same conventions, same references)
- Note: Windsurf and Cursor share the same workflow/rule structure but use different directories

### 3. Record Choice

Document the selected target(s) for DSP-05:

```
Target AI IDE Selection:
  Primary:   Windsurf
  Secondary: Claude Code
  
  Output files to generate:
    1. .windsurf/rules/ (multiple .md files)
    2. CLAUDE.md (single file)
```

### 4. Confirm Output Structure

Explain to the user what will be generated:

**For Claude Code / GitHub Copilot** (single file):
- One comprehensive Markdown file covering:
  - Project overview and architecture
  - Directory layout and docs map
  - Available workflows, skills, and artifact templates
  - AI/human collaboration patterns and quality gates
  - Coding conventions and testing discipline
  - How to build features (BPE workflow reference)
  - How to run locally

**For Windsurf / Cursor** (multiple files):
- The project already uses `.windsurf/rules/` and `.windsurf/workflows/` — these ARE the config
- DSP-05 will audit and supplement existing rules to ensure completeness
- A summary `_ai-context.md` rule file will be generated pointing to all docs, workflows, skills, and templates
- Existing rules will NOT be overwritten

---

## Deliverables

- ✅ **Target AI IDE** selected (one or more)
- ✅ **Output format** understood by user
- ✅ **Ready to proceed** to DSP-05 (Generate AI IDE Configuration)

## Agent

None

## Skill

None

## Rules

None

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
