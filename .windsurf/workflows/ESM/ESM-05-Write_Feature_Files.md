# Activity: Write Feature Files

**Activity ID**: 21
**Order**: 5
**Phase**: Specification
**Dependencies**: Predecessor: Activity 20 (Create Dialogue Maps)

## Description

Write Feature Files

## Guidance

# Write Feature Files (BDD Scenarios)

## Objective

Define testable acceptance criteria for each feature using Gherkin syntax.

## Artifacts Created

- `docs/features/act-X-{entity}/*.feature` files

## Process

### 1. Create Feature Files for Each Screen

For each Screen ID from Step 3 (Dialogue Maps), create a corresponding feature file.

**File Naming**: `{entity}-{operation}.feature` (kebab-case)
- Example: `playbooks-list-find.feature`, `playbooks-create.feature`

**Feature Title Format**:
```gherkin
Feature: FOB-{ENTITY}-{OPERATION}-{VERSION} {Description}
  As a {persona}
  I want to {action}
  So that {benefit}
```

**Scenario ID Format**: `FOB-{ENTITY}-{OPERATION}-{NN}`
- Example: `FOB-PLAYBOOKS-LIST+FIND-01`, `FOB-PLAYBOOKS-LIST+FIND-02`

### 2. Write Comprehensive Scenarios

- **Happy path scenarios** (successful operations)
- **Error handling scenarios** (validation, permissions, network errors)
- **Edge cases** (empty states, max limits, special characters)
- **Navbar integration** (navigation from/to this screen)
- **Accessibility scenarios** (keyboard navigation, screen readers)

### 3. Use Proper Gherkin Syntax

- **Given**: Set up initial state
- **When**: User action
- **Then**: Expected outcome
- **And**: Additional conditions
- Use data tables for multiple examples
- Add `data-testid` references for UI elements

## Deliverables

- ✅ Complete feature files for all CRUDLF operations
- ✅ **Feature title includes Screen ID**: `Feature: FOB-{ENTITY}-{OPERATION}-{VERSION} {Description}`
- ✅ **File naming matches operation**: `{entity}-{operation}.feature` (kebab-case)
- ✅ **Scenario IDs extend Screen ID**: `FOB-{ENTITY}-{OPERATION}-{NN}` (01, 02, etc.)
- ✅ **Feature file location**: `docs/features/act-X-{entity}/`
- ✅ **Each scenario references Screen ID from Step 3**
- ✅ **Grep-able**: `grep -r "FOB-PLAYBOOKS-LIST+FIND-1" docs/features/`
- ✅ Navbar integration scenarios
- ✅ Error handling scenarios
- ✅ Edge case coverage

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
