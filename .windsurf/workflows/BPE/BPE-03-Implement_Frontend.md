# Activity: Implement Frontend

**Activity ID**: 11
**Order**: 3
**Phase**: Implementation
**Dependencies**: Predecessor: Activity 10 (Implement Backend)

## Description

Implement Frontend

## Guidance

## Purpose
Implement frontend templates and interactions following your framework's patterns with appropriate rendering approach.

## Prerequisites
- Backend implementation completed with passing tests
- Routing defined
- Review UX/design guidelines to identify sections applicable to the page/component

## Steps

### 1. Review Routing and Template Structure
Check routing patterns - does anything need to be added or changed? Plan template/component hierarchy (base templates, partials, pages/components). Identify dynamic interactions needed.

### 2. Implement Templates/Components
**A. Page Templates/Components**: Full pages (inherit from base or layout)
**B. Partials/Components**: Reusable fragments for dynamic updates
**C. Dynamic Attributes**: Use your framework's patterns for interactions
**D. Forms**: Forms with appropriate validation and submission handling
**E. Visualizations**: Embed visualizations as appropriate for your stack

Add test IDs (`data-testid` or equivalent) to all interactive elements. Work in small increments.

### 3. Interaction Patterns
- **Navigation**: Follow your framework's navigation patterns
- **Forms**: Handle submission with validation feedback
- **Dynamic Lists**: Refresh/update lists dynamically
- **Modals/Dialogs**: Implement dialogs with dynamic content loading

Add minimal client-side code only for:
* Framework-specific enhancements
* Client-side validation enhancement
* Interactive effects (tooltips, hover, etc.)

### 4. Development Testing
Start your development server
Test in browser
Check console for errors
Verify forms submit correctly
Test visualizations render properly
Validate dynamic updates work as expected

### 5. Add Semantic Test IDs
Add `data-testid` attributes using kebab-case. Use semantic names that describe purpose, not structure. Required on: buttons, links, form inputs, containers, error messages.

### 6. Styling
Read `docs/ux/IA_guidelines.md` to identify what applies to the page/component and apply them. Use simple CSS, keep styles in static/css/, use semantic HTML elements, ensure responsive design.

### 7. Commit Changes
Commit frontend changes using Angular-style commit messages.

### 8. Integration Validation
Verify all views/controllers return correct templates/components, check dynamic interactions update correct elements, ensure forms handle validation errors properly, test visualizations render correctly, validate test IDs are present for testing.

### 9. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `FRONTEND_FRAMEWORK` — Frontend implementation patterns for your tech stack
- `UI_TESTING` — UI testing patterns and semantic naming conventions

Apply reference implementations and patterns from matched Skills.

## Rules to Follow

### I. Semantic Naming for UI Elements

**Test Selector Hierarchy:**
1. Test IDs (`data-testid` or framework equivalent) - Primary choice for all components
2. Semantic attributes (`aria-label`, role) - Secondary for semantic elements
3. Label association - For form inputs
4. Text content - Only for static, stable content
5. Avoid CSS selectors or XPath when possible

**Every interactive element MUST have:**
- Proper test ID attribute
- `aria-label` or descriptive text for buttons
- Associated label elements for form inputs
- Unique accessible names for dialogs

**Hierarchical Test ID Naming:**
- Page-Level: `{domain}-page`
- Feature Components: `{domain}-card`
- Action Elements: `{action}-{domain}-button`
- Form Elements: `{domain}-{field}-input`
- Status/Feedback: `{type}-message`

### II. Small Increments
Work in small vertical slices. After every change: write → run → test → evaluate → fix. No large PRs or 1000-line commits.

### III. UI Design Rules

**Action Buttons and Links:**
- Every action button/link should have an appropriate icon
- If no icon specified in requirements, propose 3 icon options for user to choose
- Icons should be semantically appropriate for the action

**Tooltips/Help Text:**
- Every action button should have helpful tooltip or help text
- Active buttons: Explain clearly what will happen when clicked
- Disabled buttons: Explain why it's disabled and what needs to be done to enable it
- Use your framework's tooltip/help text patterns
- Keep text concise but informative

### IV. Validation Checklist
Before committing any component, verify all interactive elements have proper attributes and accessibility features.

## Success Criteria
- All templates/components implemented with semantic markup
- Dynamic interactions working as expected
- All interactive elements have test ID attributes
- Forms handle validation errors properly
- Responsive design verified
- Code committed with proper messages

## Artifacts Produced

None

## Artifacts Consumed

- Skills from capability domains: `FRONTEND_FRAMEWORK`, `UI_TESTING`

## Notes

No additional notes.
