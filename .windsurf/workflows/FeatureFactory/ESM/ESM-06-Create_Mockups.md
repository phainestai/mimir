# Activity: Create Mockups

**Activity ID**: 40
**Order**: 6
**Phase**: Inception
**Dependencies**: None

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

## Inputs

Read these before starting this activity. They are produced earlier in the playbook and are authoritative — raise a drift event instead of deviating.

- **User Journey** (Document, Required) — produced by Define User Journey (#36).
- **IA Guidelines** (Document, Required) — produced by Define Information Architecture (#37).
- **Screen Flow / Dialogue Map** (Diagram, Required) — produced by Create Dialogue Maps (#38).

## Agent

None

## Skill

None

## Rules

- **Diagrams Element By Element** (`do-diagrams-element-by-element`)
- **Look Via Human Eye** (`do-look-via-human-eye`)
- **View Drawio Diagrams** (`do-view-drawio-diagrams`)

## Artifacts Produced

- **HTML Mockups** (Code) - Required

## Artifacts Consumed

- **User Journey** (Document) - Required
- **IA Guidelines** (Document) - Required
- **Screen Flow / Dialogue Map** (Diagram) - Required

## Notes

No additional notes.
