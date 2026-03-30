# Activity: Implement Frontend

**Activity ID**: 11
**Order**: 3
**Phase**: Implementation
**Dependencies**: Predecessor: Activity 10 (Implement Backend)

## Description

Implement Frontend

## Guidance

## Purpose
Implement Django templates and HTMX interactions with server-side rendering and minimal JavaScript.

## Prerequisites
- Backend implementation completed with passing tests
- URL routing defined
- Read `docs/ux/IA_guidelines.md` to identify sections applicable to the page/component

## Steps

### 1. Review URL Routing and Template Structure
Check Django URL patterns - does anything need to be added or changed? Plan template hierarchy (base templates, partials, pages). Identify HTMX interactions needed.

### 2. Implement Django Templates with HTMX
**A. Page Templates**: Full HTML pages (inherit from base.html)
**B. Template Partials**: HTML fragments for HTMX updates (in templates/*/partials/)
**C. HTMX Attributes**: Use hx-get, hx-post, hx-target, hx-swap for interactions
**D. Forms**: Django forms with HTMX submission
**E. Graph Visualizations**: Graphviz SVG embedded in templates

Add `data-testid` attributes to all interactive elements. Work in small increments.

### 3. HTMX Interaction Patterns
- **Navigation**: hx-get with target div swap
- **Forms**: hx-post returning updated content or form validation
- **Dynamic Lists**: hx-get to refresh list partials
- **Modals/Dialogs**: HTML dialog element with HTMX content loading

Add minimal JavaScript only for:
* Making SVG links work with HTMX
* Client-side validation enhancement
* Tooltips/hover effects

### 4. Development Testing
Start Django development server: `python manage.py runserver`
Test at http://localhost:8000
Check browser console for HTMX events and errors
Verify forms submit correctly
Test graph visualizations render properly
Validate HTMX updates work without full page reloads

### 5. Add Semantic Test IDs
Add `data-testid` attributes using kebab-case. Use semantic names that describe purpose, not structure. Required on: buttons, links, form inputs, containers, error messages.

### 6. Styling
Read `docs/ux/IA_guidelines.md` to identify what applies to the page/component and apply them. Use simple CSS, keep styles in static/css/, use semantic HTML elements, ensure responsive design.

### 7. Commit Changes
Commit frontend changes using Angular-style commit messages.

### 8. Integration Validation
Verify all Django views return correct templates, check HTMX interactions update correct target elements, ensure forms handle validation errors properly, test Graphviz SVG graphs render correctly, validate `data-testid` attributes are present for testing.

## Rules to Follow

### I. Semantic Naming for UI Elements

**Playwright Selector Hierarchy (MANDATORY ORDER):**
1. `data-testid` - Primary choice for all components
2. `aria-label` with role - Secondary for semantic elements
3. Label association - For form inputs
4. Text content - Only for static, stable content
5. NEVER use CSS selectors or XPath

**Every interactive element MUST have:**
- Proper `data-testid` attribute
- `aria-label` or descriptive text for buttons
- Associated `<label>` elements for form inputs
- Unique accessible names for dialogs

**Hierarchical data-testid Naming:**
- Page-Level: `data-testid="intents-page"`
- Feature Components: `data-testid="intent-card"`
- Action Elements: `data-testid="create-intent-button"`
- Form Elements: `data-testid="intent-name-input"`
- Status/Feedback: `data-testid="success-message"`

### II. Small Increments
Work in small vertical slices. After every change: write → run → test → evaluate → fix. No large PRs or 1000-line commits.

### III. GUI Design Rules

**Action Buttons and Links:**
- Every action button/link MUST have a Font Awesome Pro icon
- If no icon specified in requirements, propose 3 icon options for user to choose
- Icons should be semantically appropriate for the action

**Bootstrap Hover Tooltips:**
- Every action button MUST have a Bootstrap tooltip on hover
- Active buttons: Explain clearly what will happen when clicked
- Disabled buttons: Explain why it's disabled and what needs to be done to enable it
- Use Bootstrap's `data-bs-toggle="tooltip"` and `data-bs-placement` attributes
- Keep tooltip text concise but informative

### IV. Validation Checklist
Before committing any component, verify all interactive elements have proper attributes and accessibility features.

## Success Criteria
- All templates implemented with semantic HTML
- HTMX interactions working without full page reloads
- All interactive elements have `data-testid` attributes
- Forms handle validation errors properly
- Responsive design verified
- Code committed with proper messages

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
