# Activity: Process Change Request

**Activity ID**: 16
**Order**: 8
**Phase**: Change Management
**Dependencies**: None

## Description

Process Change Request

## Guidance

## Purpose
Process an enhancement or change request in a consistent, structured manner.

## Steps

### 1. Plan the Implementation

**Understand the change:**
- Identify which part of the system will be changed
- If you don't understand user intent or implementation details - DO NOT ASSUME, ASK
- Example: "It is unclear what UI element should accept values from 1-5. Shall I assume a select dropdown, or a different UI element?"

**Review and plan:**
- Identify and review feature file(s) and scenario affected: plan changes
- Read architecture (`docs/architecture/SAO.md`): identify if changes are required and which part
- Identify Models to add/extend/change
- Identify Django Views to add/extend/change (follow Backend guidance)
- Identify Django Templates to add/extend/change (follow Frontend guidance)
- Read all guidelines in `docs/architecture/SAO.md` - adjust/extend plan to incorporate specific guidance
- Plan tests to be modified/added/dropped

### 2. Present Change Implementation Plan
Create plan as .md file for user review. Ask clarification questions.

### 3. Execute the Plan
Execute the plan step by step. Commit after completing every step of the plan, but DO NOT PUSH UNTIL USER SAYS SO.

## Rules to Follow

### I. Small Increments
Work in method-by-method steps. After every change: write → run → test → evaluate → fix. Commit after each step.

### II. Test-First Development
Write tests before implementing changes. Ensure all tests pass before moving to next step.

### III. Informative Logging
Add comprehensive logging for all changes at INFO level.

### IV. Commit Convention
Follow Angular convention. Don't push until user approves.

### V. Do Not Assume
If unclear - ASK. Never guess user intent or implementation details.

## Success Criteria
- User intent clarified
- Implementation plan created and approved
- All changes executed with tests
- All commits made (but not pushed until approved)
- Tests passing

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
