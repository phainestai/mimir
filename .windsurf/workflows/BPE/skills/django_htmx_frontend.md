# Skill: Django + HTMX Frontend Implementation Patterns

**Capability Domain**: FRONTEND_FRAMEWORK
**Technology Stack**: Django+HTMX+Graphviz

## Overview

Patterns for implementing server-rendered frontends using Django templates with HTMX for dynamic interactions, minimal JavaScript, and Graphviz for visualizations. Emphasizes testability with Django test client (no browser automation needed).

## Reference Implementation

### Pattern 1: Page Templates (Full HTML Pages)

Full pages inherit from base template:

```django
{# templates/playbooks/list.html #}
{% extends "base.html" %}

{% block title %}My Playbooks{% endblock %}

{% block content %}
<div class="container" data-testid="playbooks-page">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>My Playbooks</h1>
        <a href="{% url 'playbook_create' %}" 
           class="btn btn-primary"
           data-testid="create-playbook-button"
           data-bs-toggle="tooltip"
           title="Create a new playbook">
            <i class="fa-solid fa-plus"></i> New Playbook
        </a>
    </div>
    
    <div id="playbook-list" data-testid="playbook-list">
        {% include "playbooks/partials/_playbook_table.html" %}
    </div>
</div>
{% endblock %}
```

### Pattern 2: Template Partials (HTML Fragments for HTMX)

Partials are reusable HTML fragments in `templates/*/partials/`:

```django
{# templates/playbooks/partials/_playbook_table.html #}
<table class="table" data-testid="playbooks-table">
    <thead>
        <tr>
            <th>Name</th>
            <th>Version</th>
            <th>Status</th>
            <th>Updated</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        {% for playbook in playbooks %}
        <tr data-testid="playbook-row" data-playbook-id="{{ playbook.id }}">
            <td>
                <a href="{% url 'playbook_detail' playbook.id %}"
                   hx-get="{% url 'playbook_detail' playbook.id %}"
                   hx-target="#main-content"
                   hx-push-url="true"
                   data-testid="playbook-name-link">
                    {{ playbook.name }}
                </a>
            </td>
            <td>{{ playbook.version }}</td>
            <td>
                <span class="badge bg-{{ playbook.status_color }}">
                    {{ playbook.get_status_display }}
                </span>
            </td>
            <td>{{ playbook.updated_at|date:"Y-m-d H:i" }}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary"
                        hx-get="{% url 'playbook_edit' playbook.id %}"
                        hx-target="#modal-content"
                        data-testid="edit-playbook-button"
                        data-bs-toggle="tooltip"
                        title="Edit this playbook">
                    <i class="fa-solid fa-edit"></i>
                </button>
            </td>
        </tr>
        {% empty %}
        <tr>
            <td colspan="5" class="text-center text-muted">
                No playbooks yet. Create your first one!
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

### Pattern 3: HTMX Interaction Patterns

#### Navigation (hx-get with target swap)
```django
{# Click link, swap content, update URL #}
<a href="{% url 'workflow_detail' workflow.id %}"
   hx-get="{% url 'workflow_detail' workflow.id %}"
   hx-target="#main-content"
   hx-push-url="true"
   data-testid="workflow-link">
    {{ workflow.name }}
</a>
```

#### Forms (hx-post returning updated content)
```django
{# Form submission with HTMX #}
<form hx-post="{% url 'playbook_create' %}"
      hx-target="#playbook-list"
      hx-swap="innerHTML"
      data-testid="playbook-form">
    {% csrf_token %}
    
    <div class="mb-3">
        <label for="name" class="form-label">Name *</label>
        <input type="text" 
               class="form-control" 
               id="name" 
               name="name"
               data-testid="playbook-name-input"
               required>
    </div>
    
    <div class="mb-3">
        <label for="description" class="form-label">Description</label>
        <textarea class="form-control" 
                  id="description" 
                  name="description"
                  data-testid="playbook-description-input"
                  rows="3"></textarea>
    </div>
    
    <button type="submit" 
            class="btn btn-primary"
            data-testid="save-playbook-button"
            data-bs-toggle="tooltip"
            title="Save the new playbook">
        <i class="fa-solid fa-save"></i> Save
    </button>
</form>
```

#### Dynamic Lists (hx-get to refresh partials)
```django
{# Refresh list after action #}
<button hx-get="{% url 'playbook_list_partial' %}"
        hx-target="#playbook-list"
        hx-swap="innerHTML"
        data-testid="refresh-list-button">
    <i class="fa-solid fa-refresh"></i> Refresh
</button>
```

#### Modals/Dialogs (HTML dialog with HTMX content loading)
```django
{# Base template with modal container #}
<dialog id="modal-dialog" data-testid="modal-dialog">
    <div id="modal-content"></div>
</dialog>

{# Button that loads content into modal #}
<button hx-get="{% url 'playbook_edit' playbook.id %}"
        hx-target="#modal-content"
        onclick="document.getElementById('modal-dialog').showModal()"
        data-testid="edit-button">
    Edit
</button>

{# Modal content (partial) #}
{# templates/playbooks/partials/_edit_modal.html #}
<div class="modal-header">
    <h5>Edit Playbook</h5>
    <button onclick="document.getElementById('modal-dialog').close()"
            data-testid="close-modal-button">
        <i class="fa-solid fa-times"></i>
    </button>
</div>
<div class="modal-body">
    <form hx-post="{% url 'playbook_update' playbook.id %}"
          hx-target="#playbook-list"
          hx-swap="innerHTML">
        {# form fields #}
    </form>
</div>
```

### Pattern 4: Graphviz SVG Visualization

Server-generated graphs embedded in templates:

```python
# views.py
import graphviz
from django.shortcuts import render

def workflow_diagram(request, workflow_id):
    """Render workflow as Graphviz diagram."""
    workflow = get_object_or_404(Workflow, id=workflow_id)
    
    # Create graph
    dot = graphviz.Digraph(comment=workflow.name)
    dot.attr(rankdir='TB', bgcolor='transparent')
    
    # Add nodes
    for activity in workflow.activities.all():
        dot.node(
            str(activity.id),
            activity.name,
            shape='box',
            style='filled',
            fillcolor='lightblue'
        )
    
    # Add edges (dependencies)
    for activity in workflow.activities.all():
        if activity.predecessor:
            dot.edge(str(activity.predecessor.id), str(activity.id))
    
    # Render to SVG
    svg_content = dot.pipe(format='svg').decode('utf-8')
    
    return render(request, 'workflows/diagram.html', {
        'workflow': workflow,
        'svg_content': svg_content
    })
```

```django
{# templates/workflows/diagram.html #}
<div class="workflow-diagram" data-testid="workflow-diagram">
    {{ svg_content|safe }}
</div>

<script>
// Make SVG links work with HTMX
document.querySelectorAll('.workflow-diagram svg a').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const url = this.getAttribute('href');
        htmx.ajax('GET', url, {target: '#main-content', swap: 'innerHTML'});
    });
});
</script>
```

### Pattern 5: Minimal JavaScript (Only When Needed)

Use JavaScript sparingly for:
- SVG link handling
- Client-side validation enhancement
- Tooltips/hover effects

```javascript
// static/js/app.js

// Initialize Bootstrap tooltips
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Make Graphviz SVG links work with HTMX
document.addEventListener('htmx:afterSwap', function(event) {
    if (event.detail.target.querySelector('svg')) {
        document.querySelectorAll('svg a').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const url = this.getAttribute('href');
                htmx.ajax('GET', url, {
                    target: '#main-content',
                    swap: 'innerHTML',
                    pushUrl: true
                });
            });
        });
    }
});
```

### Pattern 6: Testing Django Templates (No Browser Needed)

Test server-side rendering with Django test client:

```python
# tests/integration/test_playbook_templates.py
from django.test import TestCase, Client
from django.contrib.auth.models import User
from methodology.models import Playbook

class PlaybookTemplateTest(TestCase):
    """Test playbook templates without browser."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        
        self.playbook = Playbook.objects.create(
            name='Test Playbook',
            description='Test',
            category='test',
            author=self.user
        )
    
    def test_playbook_list_contains_playbook_name(self):
        """Test list page contains playbook name."""
        response = self.client.get('/playbooks/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Playbook')
        self.assertContains(response, 'data-testid="playbook-row"')
    
    def test_playbook_detail_returns_correct_template(self):
        """Test detail page uses correct template."""
        response = self.client.get(f'/playbooks/{self.playbook.id}/')
        
        self.assertTemplateUsed(response, 'playbooks/detail.html')
        self.assertEqual(response.context['playbook'], self.playbook)
    
    def test_htmx_request_returns_partial(self):
        """Test HTMX request returns partial template."""
        response = self.client.get(
            f'/playbooks/{self.playbook.id}/',
            HTTP_HX_REQUEST='true'  # Simulate HTMX request
        )
        
        self.assertTemplateUsed(response, 'playbooks/partials/_detail.html')
        self.assertNotContains(response, '<html>')  # No full page
    
    def test_graph_contains_all_activities(self):
        """Test Graphviz graph includes all activities."""
        workflow = Workflow.objects.create(
            name='Test Workflow',
            playbook=self.playbook
        )
        activity1 = Activity.objects.create(name='A1', workflow=workflow)
        activity2 = Activity.objects.create(name='A2', workflow=workflow)
        
        response = self.client.get(f'/workflows/{workflow.id}/diagram/')
        svg_content = response.content.decode('utf-8')
        
        self.assertIn('A1', svg_content)
        self.assertIn('A2', svg_content)
        self.assertIn('<svg', svg_content)
```

## Common Pitfalls

### ❌ Don't: Use full page reload for everything
```django
{# Wrong - full page reload #}
<a href="{% url 'playbook_detail' playbook.id %}">
    {{ playbook.name }}
</a>
```

### ✅ Do: Use HTMX for dynamic updates
```django
{# Correct - HTMX partial update #}
<a href="{% url 'playbook_detail' playbook.id %}"
   hx-get="{% url 'playbook_detail' playbook.id %}"
   hx-target="#main-content"
   hx-push-url="true">
    {{ playbook.name }}
</a>
```

### ❌ Don't: Return JSON from Django views for HTMX
```python
# Wrong - returning JSON
def playbook_list(request):
    playbooks = Playbook.objects.all()
    return JsonResponse({'playbooks': list(playbooks.values())})
```

### ✅ Do: Return HTML fragments
```python
# Correct - returning HTML
def playbook_list(request):
    playbooks = Playbook.objects.all()
    
    if request.headers.get('HX-Request'):
        # HTMX request - return partial
        return render(request, 'playbooks/partials/_list.html', {
            'playbooks': playbooks
        })
    else:
        # Regular request - return full page
        return render(request, 'playbooks/list.html', {
            'playbooks': playbooks
        })
```

### ❌ Don't: Write complex JavaScript for interactions
```javascript
// Wrong - complex JS state management
let playbooks = [];
fetch('/api/playbooks/')
    .then(r => r.json())
    .then(data => {
        playbooks = data;
        renderPlaybooks(playbooks);
    });
```

### ✅ Do: Let server handle state, use HTMX
```django
{# Correct - server-side state, HTMX updates #}
<button hx-get="{% url 'playbook_list_partial' %}"
        hx-target="#playbook-list">
    Refresh
</button>
```

### ❌ Don't: Forget data-testid attributes
```django
{# Wrong - no test IDs #}
<button class="btn btn-primary">Save</button>
<div class="playbook-list">...</div>
```

### ✅ Do: Add semantic test IDs
```django
{# Correct - semantic test IDs #}
<button class="btn btn-primary" data-testid="save-playbook-button">
    Save
</button>
<div class="playbook-list" data-testid="playbook-list">...</div>
```

## Quality Gates

Before declaring frontend implementation complete:

- [ ] All templates use semantic HTML elements
- [ ] HTMX interactions work without full page reloads
- [ ] All interactive elements have `data-testid` attributes
- [ ] Forms handle validation errors properly (server-side)
- [ ] Responsive design verified (mobile, tablet, desktop)
- [ ] All buttons have Font Awesome icons
- [ ] All buttons have Bootstrap tooltips
- [ ] Tooltips explain what will happen (active) or why disabled
- [ ] Template partials properly organized in `partials/` subdirectories
- [ ] HTMX requests detected and return partials (not full pages)
- [ ] Graphviz SVG graphs render correctly
- [ ] SVG links work with HTMX navigation
- [ ] Minimal JavaScript (only for enhancements)
- [ ] All templates tested with Django test client (no browser)
- [ ] Template context validated and documented

## Template Organization

```
templates/
├── base.html                    # Base template
├── playbooks/
│   ├── list.html               # Full page
│   ├── detail.html             # Full page
│   ├── create.html             # Full page
│   └── partials/
│       ├── _list.html          # List partial for HTMX
│       ├── _detail.html        # Detail partial for HTMX
│       ├── _form.html          # Form partial
│       └── _card.html          # Card component
├── workflows/
│   ├── detail.html
│   ├── diagram.html
│   └── partials/
│       └── _activity_list.html
└── components/
    ├── _navbar.html
    ├── _sidebar.html
    └── _modal.html
```

## HTMX Attributes Reference

- `hx-get` - Issue GET request
- `hx-post` - Issue POST request
- `hx-target` - Element to swap content into
- `hx-swap` - How to swap (innerHTML, outerHTML, beforeend, etc.)
- `hx-push-url` - Update browser URL
- `hx-trigger` - What triggers the request (click, change, etc.)
- `hx-indicator` - Loading indicator element
- `hx-confirm` - Confirmation dialog before request

## Testing Strategy

### Server-Side Template Tests (Django TestCase)
- Test template rendering
- Test context data
- Test HTMX partial responses
- Test form validation errors
- Validate SVG graph content
- No browser automation needed
- Fast (<5s per test class)
