# ACT 7: Agents CRUDLF - Parent Story

**Date**: 2026-03-30  
**Type**: Feature Implementation (Multi-Story Epic)  
**Status**: Planning  
**Implementation Strategy**: Copilot-Driven via GitHub Issues

## Executive Summary

Implement complete CRUDLF (Create, Read, Update, Delete, List, Find) functionality for Agents - AI assistants that perform activities within methodologies. This is a multi-story epic split into 3 sub-stories to stay within Copilot's complexity threshold.

## Conceptual Shift

**Agents** replace the concept of "Roles" (human job functions) with AI assistants that have:
- Specific capabilities and guidelines
- Behavioral patterns (e.g., defensive programming, test-first)
- Reference implementations (see `.github/agents/drdobbs-v2.md`)

## Feature Files

All 5 feature files exist in `docs/features/act-7-agents/`:
1. `agents-list-find.feature` - 8 scenarios
2. `agents-create.feature` - 4 scenarios  
3. `agents-view.feature` - 6 scenarios
4. `agents-edit.feature` - 4 scenarios
5. `agents-delete.feature` - 5 scenarios

**Total**: 27 scenarios across 5 CRUDLF operations

## Architecture Patterns (from SAO.md)

### Core Principles
1. **Repository Pattern**: Storage-agnostic architecture (SQLite for FOB)
2. **Service Layer**: Business logic shared between MCP and Web UI
3. **HTMX + Django**: Server-rendered UI with minimal JS
4. **Test-First**: Every function begins with a test

### Existing CRUDLF References
- **ACT 8 Skills**: 1:1 relationship with Activity (simpler model)
- **ACT 6 Artifacts**: M:1 relationship with Activity (more complex)
- **Pattern**: Model → Service → Views → Templates → Tests

## Sub-Story Split Strategy

### Why Split?

**Copilot Complexity Threshold** (from `cp-1-task-copilot.md`):
- Max 3-5 classes total
- Max 18-20 methods total

**Single Story Would Be**:
- ~6-7 classes (Model, Service, 5 Views, URLs, Forms)
- ~25-30 methods
- 27 test files
- **Verdict**: Over threshold → Split required

### Sub-Stories Overview

#### **Sub-Story 1: Agent Model + List/Find** 
- **Complexity**: 3 classes, ~12 methods ✅
- **Scenarios**: AGENT-LIST-01 through AGENT-LIST-08 (8 scenarios)
- **Deliverables**: 
  - Agent model with migration
  - AgentService (basic CRUD)
  - Global list view with search/filter
  - Empty state handling
  - 8 integration tests

#### **Sub-Story 2: Agent Create + View**
- **Complexity**: 2 classes, ~8 methods ✅
- **Scenarios**: AGENT-CREATE-01 through AGENT-CREATE-04, AGENT-VIEW-01 through AGENT-VIEW-06 (10 scenarios)
- **Dependencies**: Requires Sub-Story 1 (model must exist)
- **Deliverables**:
  - Create view + form validation
  - Detail view with activity relationships
  - Navigation between views
  - 10 integration tests

#### **Sub-Story 3: Agent Edit + Delete**
- **Complexity**: 2 classes, ~6 methods ✅
- **Scenarios**: AGENT-EDIT-01 through AGENT-EDIT-04, AGENT-DELETE-01 through AGENT-DELETE-05 (9 scenarios)
- **Dependencies**: Requires Sub-Stories 1 & 2
- **Deliverables**:
  - Edit view + form
  - Delete modal with cascade warnings
  - Activity relationship cleanup
  - 9 integration tests

## Branch Strategy

```
feature/act-7-agents (parent epic branch)
├── feature/act-7-agents/model-list-find (Sub-Story 1)
├── feature/act-7-agents/create-view (Sub-Story 2)
└── feature/act-7-agents/edit-delete (Sub-Story 3)
```

**Merge Order**:
1. `feature/act-7-agents/model-list-find` → `feature/act-7-agents`
2. `feature/act-7-agents/create-view` → `feature/act-7-agents`
3. `feature/act-7-agents/edit-delete` → `feature/act-7-agents`
4. `feature/act-7-agents` → `main` (after user acceptance)

## Copilot Workflow

Each sub-story follows this workflow:

1. **Planning** (Cascade via `@/BPE-01-Plan_Feature`):
   - Create detailed implementation plan
   - Prepare GitHub issue via `@cp-1-task-copilot.md`
   - Get user approval

2. **Implementation** (GitHub Copilot):
   - Copilot implements from GitHub issue
   - Follows red-green-refactor cycle
   - Updates task checkboxes in issue
   - Commits after each major block

3. **Review** (Cascade via `@cp-2-review-copilot-work.md`):
   - Review Copilot's PR
   - Run all tests (must be 100% pass)
   - Check Definition of Done
   - Merge or request changes

## Success Criteria (Epic Level)

- [ ] All 3 sub-stories completed and merged
- [ ] All 27 scenarios have passing tests (100% pass rate)
- [ ] Agent model registered in Django admin
- [ ] All CRUDLF operations functional in Web UI
- [ ] No broken references to "role" in codebase
- [ ] Screen flow diagram updated (already done in commit b2e0455)
- [ ] Architecture docs updated (already done in commit b2e0455)

## Timeline

- **Sub-Story 1**: Foundation (model + list) - Implement first
- **Sub-Story 2**: Core functionality (create + view) - Implement second
- **Sub-Story 3**: Maintenance operations (edit + delete) - Implement last

Each sub-story is independently reviewable and testable.

## References

- Feature Files: `docs/features/act-7-agents/*.feature`
- Architecture: `docs/architecture/SAO.md`
- Agent Example: `.github/agents/drdobbs-v2.md`
- Skills Reference: `methodology/models/skill.py`, `methodology/skill_views.py`
- Artifacts Reference: `methodology/models/artifact.py`, `methodology/artifact_views.py`
- Copilot Workflow: `.windsurf/workflows/cp-1-task-copilot.md`
- Review Workflow: `.windsurf/workflows/cp-2-review-copilot-work.md`

## Next Steps

1. Create detailed plan for Sub-Story 1 (Model + List/Find)
2. Create detailed plan for Sub-Story 2 (Create + View)
3. Create detailed plan for Sub-Story 3 (Edit + Delete)
4. Get user approval for all 3 plans
5. Create parent epic branch: `feature/act-7-agents`
6. Execute Sub-Story 1 via Copilot workflow
