# Change Request: Rename "Roles" to "Agents" (ACT 7)

**Date**: 2026-03-30  
**Type**: Terminology Change / Conceptual Refinement  
**Status**: Executing  

## Executive Summary

Rename "Roles" to "Agents" throughout the Mimir codebase to better reflect that these entities represent **AI agents** (like drdobbs-v2) that perform activities, not human job roles.

## Motivation

**Current State**: "Role" terminology suggests human job functions (e.g., "Frontend Developer", "UX Designer")

**Desired State**: "Agent" terminology represents AI assistants with specific capabilities, guidelines, and behavioral patterns that perform methodology activities

**Example**: drdobbs-v2 is a "Cautious Developer Agent" with principles like defensive programming, test-first development, and SOLID principles.

## Scope Analysis

### ✅ What EXISTS (Needs Renaming)
1. **Feature Files**: `docs/features/act-7-roles/` (5 files, 110+ references)
2. **Screen Flow Diagram**: ACT 7 section with FOB-ROLES screens (incorrectly labeled as ACT 8, not implemented, grey borders)
3. **Architecture Documentation**: References to "role" as core entity
4. **Code Comments**: TODOs mentioning "Role" model

### ❌ What DOES NOT EXIST (No Code Changes Needed)
1. **No Role Model**: No `role.py` in `methodology/models/`
2. **No Role Views**: No implementation in `methodology/views/`
3. **No Role URLs**: No routes defined
4. **No Role Templates**: No HTML templates
5. **No Role Services**: No business logic
6. **No Role Tests**: No test files
7. **No Database Tables**: No migrations needed

**Conclusion**: This is a **documentation-only rename** since Roles/Agents are not yet implemented in code.

## Impact Assessment

### High Impact (Must Change)
- ✅ Feature files (5 files)
- ✅ Screen flow diagram (ACT 8 section)
- ✅ Architecture documentation (SAO.md)

### Medium Impact (Should Change)
- ✅ Workflow documentation references
- ✅ Code comments/TODOs

### Low Impact (Optional)
- ⚠️ Git history (will show "roles" in old commits - acceptable)

### No Impact
- ✅ Database (no migrations needed)
- ✅ Running code (nothing implemented yet)
- ✅ Tests (none exist)

## Detailed Changes

### 1. Feature Files (`docs/features/act-7-roles/` → `docs/features/act-7-agents/`)

**Directory Rename**: `act-7-roles` → `act-7-agents` (Keep ACT 7 numbering - ACT 8 is Skills)

**Files to Rename**:
- `roles-list-find.feature` → `agents-list-find.feature`
- `roles-create.feature` → `agents-create.feature`
- `roles-view.feature` → `agents-view.feature`
- `roles-edit.feature` → `agents-edit.feature`
- `roles-delete.feature` → `agents-delete.feature`

**Content Changes** (per file):
- Feature titles: `FOB-ROLES-*` → `FOB-AGENTS-*`
- Scenario IDs: `ROLE-*` → `AGENT-*`
- User stories: "roles" → "agents"
- Field names: "role" → "agent"
- Descriptions: Update to reflect AI agent concept

**Example Transformation**:
```gherkin
# BEFORE
Feature: FOB-ROLES-CREATE_ROLE-1 Create Role
  As a methodology author (Maria)
  I want to create roles within a playbook
  So that I can define team member responsibilities

# AFTER
Feature: FOB-AGENTS-CREATE_AGENT-1 Create Agent
  As a methodology author (Maria)
  I want to create agents within a playbook
  So that I can define AI assistants that perform activities
```

### 2. Screen Flow Diagram (`docs/ux/2_dialogue-maps/screen-flow.drawio`)

**Changes Required**:
- Line 1032: `ACT 8: ROLES` → `ACT 7: AGENTS` (Fix incorrect ACT numbering)
- Lines 1035-1049: All `FOB-ROLES-*` → `FOB-AGENTS-*`
- Lines 1053-1070: All `@*_role` tools → `@*_agent`
- Update labels: "role" → "agent" in all text

**Specific Updates**:
```xml
<!-- BEFORE -->
<mxCell id="v2-act8-label" value="ACT 8: ROLES" .../>
<mxCell id="v2-fob-roles-list" value="FOB-ROLES-&#10;LIST+FIND" .../>
<mxCell id="v2-tool-create-role" value="@create_role" .../>

<!-- AFTER -->
<mxCell id="v2-act7-label" value="ACT 7: AGENTS" .../>
<mxCell id="v2-fob-agents-list" value="FOB-AGENTS-&#10;LIST+FIND" .../>
<mxCell id="v2-tool-create-agent" value="@create_agent" .../>
```

### 3. Architecture Documentation (`docs/architecture/SAO.md`)

**Changes Required**:

**Line 985**: Update activity label format
```markdown
# BEFORE
label = f"{activity.name}\\n({activity.role.name})"

# AFTER
label = f"{activity.name}\\n({activity.agent.name})"
```

**Line 1092-1093**: Update context dictionary
```python
# BEFORE
'role': activity.role

# AFTER
'agent': activity.agent
```

**Line 1319**: Update feature directory listing
```markdown
# BEFORE
├── act-7-roles/             # Roles CRUDLF (5 files)

# AFTER
├── act-7-agents/            # Agents CRUDLF (5 files)
```

**Line 1410**: Update core entities list
```python
# BEFORE
# 7 Core Entities: 'playbook', 'workflow', 'phase', 'activity', 
# 'artifact', 'role', 'skill'

# AFTER
# 7 Core Entities: 'playbook', 'workflow', 'phase', 'activity', 
# 'artifact', 'agent', 'skill'
```

**Line 1427**: Update relationship type
```python
# BEFORE
# 'performed_by_role', 'guided_by_skill',

# AFTER
# 'performed_by_agent', 'guided_by_skill',
```

**Lines 1890-1892**: Update entity description
```markdown
# BEFORE
**Role**: Who performs activities
- Example: "Frontend Engineer", "UX Designer"
- Can be: Human, AI agent, or hybrid

# AFTER
**Agent**: AI assistant that performs activities
- Example: "Cautious Developer (drdobbs-v2)", "UX Researcher Agent"
- Each agent has specific capabilities, guidelines, and behavioral patterns
- Reference: .github/agents/ for agent definitions
```

**Line 1970**: Update web UI reference
```markdown
# BEFORE
- Simple web UI for viewing Playbooks, Workflows, Activities, Skills, Artifacts, Roles

# AFTER
- Simple web UI for viewing Playbooks, Workflows, Activities, Skills, Artifacts, Agents
```

### 4. Code Comments (`methodology/`)

**playbook_views.py** (Line 560):
```python
# BEFORE
# - Roles

# AFTER
# - Agents
```

**models/playbook.py** (Line 157):
```python
# BEFORE
'roles': 0,  # TODO: Implement when Role model exists

# AFTER
'agents': 0,  # TODO: Implement when Agent model exists
```

### 5. Workflow Documentation

**Update finalize feature workflow** (`BPE-07-Finalize_Feature.md` step 8):
```markdown
# BEFORE
- Change `strokeColor=#1565c0` to `strokeColor=#22c55e` (green)

# AFTER
- Change `strokeColor=#1565c0` to `strokeColor=#22c55e` (green)
- Update ACT labels if entity names changed (e.g., Roles → Agents)
```

## Implementation Plan

### Phase 1: Documentation Updates (No Code Impact)

**Step 1**: Rename feature directory
```bash
git mv docs/features/act-7-roles docs/features/act-7-agents
```

**Step 2**: Rename feature files
```bash
cd docs/features/act-7-agents
git mv roles-list-find.feature agents-list-find.feature
git mv roles-create.feature agents-create.feature
git mv roles-view.feature agents-view.feature
git mv roles-edit.feature agents-edit.feature
git mv roles-delete.feature agents-delete.feature
```

**Step 3**: Update feature file content (5 files)
- Use multi_edit or edit tool for each file
- Replace all instances of role/Role with agent/Agent
- Update scenario IDs, feature names, descriptions

**Step 4**: Update screen flow diagram
- Use multi_edit to update all references
- Fix ACT 8 → ACT 7 (correct numbering)
- Update labels, IDs, tool names (ROLES → AGENTS)

**Step 5**: Update architecture documentation
- Update SAO.md with all identified changes
- Update entity descriptions to reflect AI agent concept

**Step 6**: Update code comments
- Update TODOs in playbook_views.py and playbook.py

**Step 7**: Commit changes
```bash
git add -A
git commit -m "refactor(terminology): rename Roles to Agents (ACT 7)

- Rename act-7-roles → act-7-agents feature directory
- Update all feature files: FOB-ROLES-* → FOB-AGENTS-*
- Update screen flow diagram: ACT 8 ROLES → ACT 7 AGENTS (fix numbering)
- Update architecture docs: role → agent terminology
- Update code comments and TODOs
- Reflect conceptual shift: human roles → AI agents

BREAKING CHANGE: Feature file scenario IDs changed from ROLE-* to AGENT-*

Refs: .github/agents/drdobbs-v2.md for agent concept example"
```

## Verification Checklist

- [ ] All 5 feature files renamed and updated
- [ ] Feature directory renamed (act-7-roles → act-8-agents)
- [ ] Screen flow diagram ACT 8 section updated
- [ ] Architecture documentation updated (7 locations)
- [ ] Code comments updated (2 locations)
- [ ] No broken references to "role" in documentation
- [ ] Commit message follows Angular convention
- [ ] All changes committed (not pushed until user approval)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing references | Low | No code implemented yet, only docs |
| Confusion with old commits | Low | Git history preserved, clear commit message |
| Inconsistent terminology | Medium | Comprehensive search and replace |
| Missing references | Low | Thorough grep search before commit |

## Questions for User

1. ✅ **Confirmed**: Agents are AI assistants (like drdobbs-v2), not human roles
2. ✅ **Confirmed**: This is ACT 7 (ACT 8 is Skills) - keep ACT 7 numbering
3. ✅ **Confirmed**: Directory remains `act-7-agents` (screen flow incorrectly labeled as ACT 8)

## Success Criteria

- ✅ All documentation uses "Agent" terminology consistently
- ✅ Feature files reflect AI agent concept (not human roles)
- ✅ Screen flow diagram updated
- ✅ Architecture docs updated
- ✅ No code changes required (nothing implemented yet)
- ✅ Single atomic commit with clear message
- ✅ User approval obtained before push

## Next Steps

1. **User Review**: Get approval on this plan
2. **Execute**: Implement all changes per plan
3. **Verify**: Run through checklist
4. **Commit**: Single commit with all changes
5. **Await**: User approval before push
