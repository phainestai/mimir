# Activity: Review & Commit

**Activity ID**: TBD
**Order**: 6
**Phase**: Finalization
**Dependencies**: Predecessor: DSP-05 (Generate AI IDE Configuration)

## Description

Review & Commit

## Guidance

# Review & Commit

## Objective

Review the generated AI IDE configuration file(s) with the user, make any requested adjustments, and commit to the repository.

---

## Process

### 1. Present Generated Config for Review

Show the user the generated file(s) from DSP-05:

**For each generated file, verify:**

| Check | Criteria |
|-------|----------|
| **Completeness** | All 10 sections present and populated |
| **Accuracy** | Architecture matches current SAO.md |
| **Docs Map** | All referenced files actually exist |
| **Workflows** | All available workflows listed |
| **Skills** | All available skills listed (or "none yet" noted) |
| **Artifact Templates** | All templates referenced with correct paths |
| **Conventions** | Coding standards match team practice |
| **Running Locally** | Commands are correct and tested |

### 2. Collect User Feedback

Ask the user:

1. **Is anything missing?** — project-specific conventions, team norms, special tools?
2. **Is anything wrong?** — outdated architecture, incorrect paths, stale conventions?
3. **Is anything unnecessary?** — sections that add noise without value?
4. **Tone and style** — too verbose? Too terse? Right level of detail?

### 3. Apply Adjustments

Make requested changes to the generated file(s). Common adjustments:

- Add project-specific environment variables or secrets handling
- Add team-specific review processes
- Adjust emphasis on certain workflows over others
- Add links to external resources (CI/CD dashboards, design tools, etc.)

### 4. Validate File Locations

Confirm files are in the correct locations:

| Target | Expected Location | Exists? |
|--------|-------------------|---------|
| Claude Code | `CLAUDE.md` (project root) | ✅/❌ |
| GitHub Copilot | `.github/copilot-instructions.md` | ✅/❌ |
| Windsurf | `.windsurf/rules/_ai-context.md` | ✅/❌ |
| Cursor | `.cursor/rules/_ai-context.mdc` | ✅/❌ |

### 5. Commit

Commit the generated config file(s) with:

```
docs(dsp): generate AI IDE configuration for {target}

- Generated {filename} from SAO.md, ESM artifacts, and workflow inventory
- Includes: architecture, docs map, workflows, skills, artifact templates,
  AI/human collaboration patterns, coding conventions, BPE workflow reference
- Target IDE: {Claude Code | GitHub Copilot | Windsurf | Cursor}
```

---

## Deliverables

- ✅ **Config file(s) reviewed** by user
- ✅ **Adjustments applied** per user feedback
- ✅ **File locations validated**
- ✅ **Committed to repository**
- ✅ **AI IDE ready** to consume project context and start building features

## Artifacts Produced

- Committed AI IDE configuration file(s)

## Artifacts Consumed

- Generated config file(s) from DSP-05
- User feedback

## Notes

After this activity, the AI agent (Claude Code, Copilot, Windsurf, or Cursor) should be able to:
1. Understand the project architecture and conventions
2. Find and read feature specs for any Act
3. Know which workflows to follow for different tasks
4. Reference skills for technology-specific guidance
5. Use artifact templates for consistent output
6. Follow the right coding conventions and testing discipline

**Test the setup:** After committing, open a new AI conversation and ask it to implement a simple feature. Verify it references the correct docs, follows the right workflow, and produces code matching project conventions. If it doesn't — iterate on the config.