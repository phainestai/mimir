# Activity: Feed into Implementation

**Activity ID**: 23
**Order**: 7
**Phase**: Development
**Dependencies**: Predecessor: Activity 22 (Create Mockups)

## Description

Feed into Implementation

## Guidance

# Feed into Feature Implementation Workflow

## Objective

Transition from UX design to full backend implementation using the "Build Feature" workflow (BPE-1).

## Process

### 1. Invoke "Build Feature" Workflow (BPE-1)

- Reference the feature file created in Activity 5 (Write Feature Files)
- Use mockups from Activity 6 (Create Mockups) as UI reference
- Follow the complete "Build Feature" workflow starting with BPE-1

### 2. Handoff Checklist

Ensure all UX artifacts are complete before implementation:

**Activity 1 → Activity 2**:
- [ ] Screen ID convention understood
- [ ] Traceability requirements clear
- [ ] Important guidelines reviewed

**Activity 2 → Activity 3**:
- [ ] User journey documented
- [ ] All Acts defined with personas
- [ ] Screen IDs assigned to all screens

**Activity 3 → Activity 4**:
- [ ] IA guidelines documented
- [ ] Design system tokens defined
- [ ] Navigation structure clear

**Activity 4 → Activity 5**:
- [ ] Domain model diagram complete
- [ ] MVP flow diagram shows all screens
- [ ] Screen states documented
- [ ] Flow validated visually (human eye check)

**Activity 5 → Activity 6**:
- [ ] All CRUDLF feature files written
- [ ] Scenarios follow BDD best practices
- [ ] Navbar integration scenarios added
- [ ] Error/edge cases covered

**Activity 6 → Activity 7**:
- [ ] All mockup templates created
- [ ] Mock views functional
- [ ] All UI states represented
- [ ] Accessibility attributes present
- [ ] `data-testid` attributes added
- [ ] Design system compliance verified

**Activity 7 → BPE-1 Handoff**:
- [ ] All UX artifacts complete (Activities 1-6)
- [ ] Feature files ready for implementation
- [ ] Mockups ready for conversion to real views
- [ ] Screen IDs documented across all artifacts
- [ ] Ready to start "Build Feature" workflow

### 3. Traceability Verification

Verify Screen ID appears in all 5 artifacts:
1. ✅ User Journey (section header)
2. ✅ Screen Flow Diagram (box label)
3. ✅ Feature File (feature title)
4. ✅ Template (HTML comment + hidden div)
5. ✅ Tests (test names + docstrings)

**Grep Test**: `grep -r "FOB-{ENTITY}-{OPERATION}-{VERSION}" .`

## Deliverables

- ✅ All UX artifacts complete (Activities 1-6)
- ✅ Feature files ready for BPE-1
- ✅ Mockups ready for implementation
- ✅ **Screen ID traceability complete**: Screen ID appears in User Journey, Screen Flow, Feature File, Template, and Tests
- ✅ **Grep-able across UX artifacts**: `grep -r "FOB-{ENTITY}-{OPERATION}-{VERSION}" docs/`
- ✅ Handoff checklist verified
- ✅ Ready to invoke "Build Feature" workflow (BPE-1)

## Next Steps

After completing this activity, proceed to:
→ **"Build Feature" Workflow → Activity 1 (BPE-1)**

The "Build Feature" workflow will handle:
- Implementation planning
- Backend development (models, services, views)
- Frontend development (templates, HTMX)
- Test-first development
- 100% test pass rate
- GitHub issue management
- Feature deployment

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
