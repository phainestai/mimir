# Activity: Verify ESM Artifacts

**Activity ID**: TBD
**Order**: 1
**Phase**: Prerequisite Check
**Dependencies**: None (first activity)

## Description

Verify ESM Artifacts

## Guidance

# Verify ESM Artifacts

## Objective

Verify that all required artifacts from the **Envision the System (ESM)** workflow exist before proceeding to AI IDE configuration. If any are missing, direct the user to run the ESM workflow first.

---

## Process

### 1. Scan for Required ESM Artifacts

Check for the existence and non-emptiness of:

| Artifact | Expected Location | ESM Activity |
|----------|-------------------|--------------|
| **User Journey** | `docs/features/user_journey.md` | ESM-02 |
| **Dialogue Maps / Screen Flows** | `docs/ux/` (at least one `.drawio` or screen flow file) | ESM-04 |
| **Feature Files** | `docs/features/act-*/` (at least one `.feature` file or scenario markdown) | ESM-05 |
| **IA Guidelines** | `docs/ux/IA_guidelines.md` | ESM-03 |

### 2. Evaluate Results

For each artifact, report status:

```
ESM Artifact Check:
  User Journey              | ✅ Found (docs/features/user_journey.md, 104KB)
  Dialogue Maps             | ✅ Found (docs/ux/2_dialogue-maps/, 3 files)
  Feature Files             | ✅ Found (docs/features/act-*/,  12 acts)
  IA Guidelines             | ❌ Missing
```

### 3. If Any Missing → Redirect to ESM

If one or more artifacts are missing:

> **⚠️ ESM artifacts incomplete.**
> The following are missing: {list}.
> Please run the **Envision the System (ESM)** workflow first.
> See: `.windsurf/workflows/ESM/_workflow.md`

**Stop here** — do not proceed to DSP-02 until all ESM artifacts are present.

### 4. If All Present → Proceed

> **✅ All ESM artifacts verified.** Proceeding to DSP-02 (Verify DTA Artifacts).

---

## Deliverables

- ✅ **ESM artifact checklist** evaluated
- ✅ **All artifacts present** — or user redirected to ESM workflow
- ✅ **Ready to proceed** to DSP-02

## Artifacts Produced

- ESM verification report (pass/fail per artifact)

## Artifacts Consumed

- `docs/features/user_journey.md`
- `docs/ux/` directory contents
- `docs/features/act-*/` directory contents
- `docs/ux/IA_guidelines.md`

## Notes

This is a gate activity. It does not produce design artifacts — it only validates that the ESM workflow has been completed. If the user has partial artifacts (e.g., user journey exists but no feature files), they should complete the specific missing ESM activities rather than re-running the entire ESM workflow.
