# Activity: Establish Conventions

**Activity ID**: 17
**Order**: 1
**Phase**: Foundation
**Dependencies**: None

## Description

Establish Conventions

## Guidance

# Establish Conventions

## Objective

Establish the foundational conventions and standards that will be used throughout the entire UX design-to-development process. This includes the Screen ID naming convention for traceability and other important guidelines.

---

## Screen ID Convention (Traceability)

**All screens must follow a consistent naming pattern for end-to-end traceability.**

### Format: `FOB-{ENTITY}-{OPERATION}-{VERSION}`

**Components**:
- `FOB` = Forward Operating Base (the web UI)
- `{ENTITY}` = Uppercase entity name (PLAYBOOKS, WORKFLOWS, ACTIVITIES, etc.)
- `{OPERATION}` = Screen operation type (see CRUDLF patterns below)
- `{VERSION}` = Version number (usually `-1` for MVP)

### CRUDLF Operations

**Standard CRUD + List/Find pattern**:
- `LIST+FIND` - Entry point screen for entity (list view with search/filter)
- `CREATE_{ENTITY}` - Creation form screen
- `VIEW_{ENTITY}` - Detail/read-only view screen
- `EDIT_{ENTITY}` - Edit form screen
- `DELETE_{ENTITY}` - Deletion confirmation screen

**Examples**:
- `FOB-PLAYBOOKS-LIST+FIND-1` → Playbooks list with search/filter
- `FOB-PLAYBOOKS-CREATE_PLAYBOOK-1` → Create new playbook form
- `FOB-PLAYBOOKS-VIEW_PLAYBOOK-1` → View playbook details
- `FOB-PLAYBOOKS-EDIT_PLAYBOOK-1` → Edit playbook form
- `FOB-PLAYBOOKS-DELETE_PLAYBOOK-1` → Delete playbook confirmation
- `FOB-WORKFLOWS-LIST+FIND-1` → Workflows list (within playbook)
- `FOB-HOWTOS-CREATE_HOWTO-1` → Create howto form

### Traceability Chain

**Every Screen ID must appear in ALL of these artifacts**:

1. **User Journey** (`docs/features/user_journey.md`)
   - Format: `#### Screen: FOB-{ENTITY}-{OPERATION}-{VERSION}`
   - Describes layout, actions, user flow

2. **Screen Flow Diagram** (`docs/ux/2_dialogue-maps/screen-flow.drawio`)
   - Box label: `FOB-{ENTITY}-{OPERATION}-{VERSION}`
   - Bold border for LIST+FIND entry points
   - Navigation arrows between screens

3. **Feature File** (`docs/features/act-X-{entity}/{entity}-{operation}.feature`)
   - Feature title: `Feature: FOB-{ENTITY}-{OPERATION}-{VERSION} {Description}`
   - Scenario IDs: `FOB-{ENTITY}-{OPERATION}-{NN}` (01, 02, 03...)
   - File naming: `{entity}-{operation}.feature` (kebab-case)

4. **Template** (`templates/{entity}/{operation}.html`)
   - HTML comment: `<!-- Screen: FOB-{ENTITY}-{OPERATION}-{VERSION} -->`
   - Hidden div: `<div data-testid="{entity}-{operation}-loaded" style="display: none;">{SCREEN_ID}</div>`
   - Enables grep discovery: `grep -r "FOB-PLAYBOOKS-LIST+FIND-1" .`

5. **Tests** (`tests/integration/test_{entity}_{operation}.py`)
   - Test names reference Screen ID
   - Docstrings include Screen ID

### Benefits

✅ **Bidirectional Traceability**: Navigate from code → design or design → code  
✅ **Quick Discovery**: `grep -r "FOB-PLAYBOOKS-LIST+FIND-1" .` finds all related artifacts  
✅ **Consistency Validation**: Verify all screens have complete documentation  
✅ **Onboarding**: New developers can trace any screen to design intent  
✅ **Gap Detection**: Missing Screen IDs indicate incomplete UX work

---

## Important Notes

### What NOT to Do
- ❌ Do NOT create .MD files unless explicitly part of task definition, workflow, or rule
- ❌ Do NOT skip the planning step - always show plan and get approval
- ❌ Do NOT create massive documents or commits in one go
- ❌ Do NOT declare features complete with failing tests
- ❌ Do NOT mock in integration tests
- ❌ Do NOT skip accessibility attributes or tooltips
- ❌ Do NOT use vague naming or generic values in scenarios

### What TO Do
- ✅ Follow plan-then-do at every step
- ✅ Work incrementally - small vertical slices
- ✅ Write tests before implementation
- ✅ Maintain 100% test pass rate
- ✅ Use existing patterns and conventions
- ✅ Prioritize accessibility (ARIA, semantic HTML, keyboard navigation)
- ✅ Ensure testability (`data-testid` on all interactive elements)
- ✅ Validate diagrams visually with human eye
- ✅ Add Font Awesome Pro icons and Bootstrap tooltips to all buttons
- ✅ Check for existing GitHub issues before creating new ones
- ✅ Commit after each major step with Angular convention

---

## Deliverables

- ✅ **Screen ID convention understood and documented**
- ✅ **Traceability chain requirements clear**
- ✅ **Important guidelines reviewed**
- ✅ **Ready to proceed with User Journey definition**

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
