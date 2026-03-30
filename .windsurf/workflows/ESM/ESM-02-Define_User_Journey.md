# Activity: Define User Journey

**Activity ID**: 18
**Order**: 2
**Phase**: Design
**Dependencies**: Predecessor: Activity 17 (Establish Conventions)

## Description

Define User Journey

## Guidance

# Define User Journey

## Objective

Establish the high-level user experience narrative with personas, user flows, and screen descriptions.

## Artifacts Created

- `docs/features/user_journey.md` - Complete user journey narrative

## Process

### 1. Write User Journey Document

- Define personas (e.g., Mike Chen, Maria Rodriguez)
- Map out Acts (Act 0: Authentication → Act 9: PIPs, etc.)
- Describe user goals, motivations, and context for each Act
- Identify key screens and user flows
- Document system architecture notes (FOB vs HB, MCP integration)
- Follow narrative structure: Context → Screen → Actions → Results

**Template**:

```markdown
### Act X: [ENTITY] - Complete CRUDLF

**Context**: [User situation and needs]

**Pattern**: [Entity] follows the standard CRUDLF pattern with LIST+FIND as the entry point.

#### Screen: FOB-[ENTITY]-LIST+FIND-1

[User] clicks "[Entity]" in the main navigation. The [entity] list page appears:

**Layout**:
- **Header**: "[Entity]" with count badge (e.g., "[Entity] (3)")
- **Top Actions**:
  - [Create New [Entity]] button (primary action, bold blue)
  - [Additional Action] button
- **Search & Filter Section**:
  - Search box: "Find [entity]..." (searches [fields])
  - Filters: [Filter1], [Filter2], [Filter3]
  - [Clear Filters] button
- **[Entity] Table** with columns:
  - [Column1] | [Column2] | [Column3] | Actions
  - Sort by any column
- **Row Actions** (dropdown menu per [entity]):
  - [View] - Opens FOB-[ENTITY]-VIEW_[ENTITY]
  - [Edit] - Opens FOB-[ENTITY]-EDIT_[ENTITY]
  - [Delete] - Opens FOB-[ENTITY]-DELETE_[ENTITY] modal
  - [...More] - Additional actions
- **Empty State** (if no [entity]):
  - Illustration: [Description]
  - "No [entity] yet"
  - "[Call to action message]"
  - [Action Buttons]
- **Pagination**: Shows 20 per page with page controls

**Example Data**:
- "[Example 1]" | [Data] | [Data] | [Status]
- "[Example 2]" | [Data] | [Data] | [Status]

[User] sees [description of what user can do].
```

## How to Execute This Step

### 1. Plan Before Executing (plan-then-do)
- Identify all affected documents, sections, and artifacts
- Figure out what content you need and what's available to reference
- Note what needs to be created from scratch
- ALWAYS show the plan and ask for approval or refinements
- Execute the plan, adjusting as necessary based on discoveries
- After every major section, update the plan and explain next step

### 2. Work Incrementally (small-increments)
- Work section-by-section (one Act at a time for user journey)
- After every change: write → review → refine → evaluate
- No massive documents created in one go
- Build incrementally: personas → Act 0 → Act 1 → Act 2, etc.

## Deliverables

- ✅ Complete user journey with all Acts documented
- ✅ **Each screen uses Screen ID format**: `#### Screen: FOB-{ENTITY}-{OPERATION}-{VERSION}`
- ✅ **Screen IDs follow CRUDLF pattern**: LIST+FIND, CREATE_{ENTITY}, VIEW_{ENTITY}, EDIT_{ENTITY}, DELETE_{ENTITY}
- ✅ **Entry point screens (LIST+FIND) clearly marked**
- ✅ **Screen IDs are unique and traceable**

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
