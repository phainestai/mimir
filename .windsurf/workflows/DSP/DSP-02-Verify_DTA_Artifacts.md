# Activity: Verify DTA Artifacts

**Activity ID**: TBD
**Order**: 2
**Phase**: Prerequisite Check
**Dependencies**: Predecessor: DSP-01 (Verify ESM Artifacts)

## Description

Verify DTA Artifacts

## Guidance

# Verify DTA Artifacts

## Objective

Verify that the **System Architecture Overview (SAO.md)** from the **Define Architecture (DTA)** workflow exists and contains the required architectural decisions. If missing, direct the user to run the DTA workflow first.

---

## Process

### 1. Scan for SAO.md

Check for existence and non-emptiness of:

| Artifact | Expected Location | DTA Activity |
|----------|-------------------|--------------|
| **SAO.md** | `docs/architecture/SAO.md` | DTA-18 |

### 2. Validate SAO.md Content

If the file exists, verify it contains key sections (search for headings):

| Required Section | Purpose | Used By DSP-05 |
|-----------------|---------|-----------------|
| **Executive Summary** | Project overview for AI config | Yes — project description |
| **System Architecture** | High-level components | Yes — architecture section |
| **Design Principles** | Key decisions | Yes — coding conventions |
| **Technology Stack** or equivalent | Languages, frameworks, tools | Yes — tech stack reference |
| **Project Structure** | Directory layout | Yes — directory map |
| **Testing Infrastructure** | Test strategy | Yes — testing conventions |

Report status:

```
DTA Artifact Check:
  SAO.md exists              | ✅ Found (docs/architecture/SAO.md, 2671 lines)
  Executive Summary          | ✅ Present
  System Architecture        | ✅ Present
  Design Principles          | ✅ Present
  Technology Stack           | ❌ Missing — no explicit tech stack table
  Project Structure          | ✅ Present
  Testing Infrastructure     | ✅ Present
```

### 3. If SAO.md Missing or Incomplete → Redirect to DTA

If SAO.md does not exist:

> **⚠️ SAO.md not found.**
> Please run the **Define Architecture (DTA)** workflow first.
> See: `.windsurf/workflows/DTA/_workflow.md`

If SAO.md exists but is missing key sections:

> **⚠️ SAO.md incomplete.**
> Missing sections: {list}.
> Please complete the relevant DTA activities: {activity list}.

**Stop here** — do not proceed to DSP-03 until SAO.md is complete.

### 4. If Complete → Proceed

> **✅ SAO.md verified with all required sections.** Proceeding to DSP-03 (Verify Architecture & Code Organization).

---

## Deliverables

- ✅ **SAO.md existence** verified
- ✅ **SAO.md content** validated for required sections
- ✅ **All sections present** — or user redirected to DTA workflow
- ✅ **Ready to proceed** to DSP-03

## Artifacts Produced

- DTA verification report (pass/fail per section)

## Artifacts Consumed

- `docs/architecture/SAO.md`

## Notes

SAO.md is the single most important input for DSP-05 (Generate AI IDE Configuration). The AI config file will extract project overview, architecture, directory layout, tech stack, and testing strategy directly from SAO.md. If SAO.md is thin or incomplete, the generated config will be correspondingly weak.
