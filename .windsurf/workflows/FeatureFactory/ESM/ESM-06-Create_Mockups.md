# Activity: Create Mockups

**Activity ID**: TBD
**Order**: 6
**Phase**: Prototyping
**Dependencies**: Predecessor: Activity 21 (Write Feature Files)

## Description

Create Mockups

## Guidance

# Create Mockups (Prototyped Screens)

## Objective

Build functional prototypes with mocked data to validate UX before full implementation.

## Artifacts Created

- Django templates in `templates/entity/`
- Mock views in `entity/views.py`
- Mock data fixtures

## Process

### 1. Create Template Structure

**File Location**: `templates/{entity}/{operation}.html`
- Example: `templates/playbooks/list.html`, `templates/playbooks/create.html`

**Template Header**:
```html
<!-- Screen: FOB-{ENTITY}-{OPERATION}-{VERSION} -->
{% extends "base.html" %}
{% load static %}

{% block title %}{Page Title}{% endblock %}

{% block content %}
<!-- Main content -->
<div data-testid="{entity}-{operation}-loaded" style="display: none;">{SCREEN_ID}</div>
```

### 2. Implement UI Components

- Use Bootstrap 5.3+ components
- Add Font Awesome Pro icons to all buttons
- Add Bootstrap tooltips to all interactive elements
- Include `data-testid` attributes on all interactive elements
- Implement all UI states (loading, empty, error, success)
- Follow IA guidelines from Step 2

### 3. Create Mock Views

- Create Django view functions that return templates
- Use mock data (hardcoded or fixtures)
- No business logic - just render templates
- Add URL patterns

### 4. Add Accessibility

- Semantic HTML (nav, main, section, article)
- ARIA labels and roles
- Keyboard navigation support
- Focus management

## Deliverables

- ✅ Functional mockup templates for all screens
- ✅ **Template file comment includes Screen ID**: `<!-- Screen: FOB-{ENTITY}-{OPERATION}-{VERSION} -->`
- ✅ **Hidden div with screen ID**: `<div data-testid="{entity}-{operation}-loaded" style="display: none;">{SCREEN_ID}</div>`
- ✅ **Template location**: `templates/{entity}/{operation}.html`
- ✅ **Grep-able**: `grep -r "FOB-PLAYBOOKS-LIST+FIND-1" templates/`
- ✅ **Screen ID enables quick discovery of implementation**
- ✅ Mock views returning templates
- ✅ All UI states represented
- ✅ Proper accessibility attributes
- ✅ Testable with `data-testid` attributes

## Artifacts Produced

- `templates/{entity}/{operation}.html` — Django HTML mockup templates (one per screen, with Screen ID comment, `data-testid` attributes, all UI states)
- `{entity}/views.py` — mock Django view functions returning templates with hardcoded/fixture data
- Mock data fixtures (inline or `fixtures/`) — sample data for rendering the mockup

## Artifacts Consumed

- `docs/features/act-X-{entity}/*.feature` (from ESM-05) — defines UI elements, states, and interactions each template must represent
- `docs/ux/2_dialogue-maps/screen-flow.drawio` (from ESM-04) — provides navigation arrows to implement links between templates
- `docs/ux/IA_guidelines.md` (from ESM-03) — Bootstrap components, icon system, and accessibility patterns to apply

## Notes

No additional notes.
