# Skill: Django Backend Implementation Patterns

**Capability Domain**: BACKEND_FRAMEWORK
**Technology Stack**: Django+Python+pytest

## Overview

Comprehensive patterns for implementing Django backend services following test-first development, repository pattern, and service layer architecture. Covers models, views, services, URL routing, and testing with Django TestCase and pytest.

## Reference Implementation

### Pattern 1: Django Views Architecture

Django views should return rendered HTML templates (NOT JSON/DRF):

```python
# methodology/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .services.playbook_service import PlaybookService

@login_required
def playbook_list(request):
    """List all playbooks for current user."""
    service = PlaybookService()
    playbooks = service.get_user_playbooks(request.user)
    
    return render(request, 'playbooks/list.html', {
        'playbooks': playbooks,
        'page_title': 'My Playbooks'
    })

@login_required
def playbook_create(request):
    """Create new playbook."""
    if request.method == 'POST':
        service = PlaybookService()
        try:
            playbook = service.create_playbook(
                name=request.POST['name'],
                description=request.POST['description'],
                category=request.POST['category'],
                author=request.user
            )
            messages.success(request, f'Playbook "{playbook.name}" created successfully')
            return redirect('playbook_detail', playbook_id=playbook.id)
        except ValidationError as e:
            messages.error(request, str(e))
    
    return render(request, 'playbooks/create.html')
```

### Pattern 2: Services Layer (Business Logic)

Business logic shared between MCP and Web UI lives in services:

```python
# methodology/services/playbook_service.py
from django.core.exceptions import ValidationError
from decimal import Decimal
from ..models import Playbook

class PlaybookService:
    """Business logic for playbook management."""
    
    @staticmethod
    def create_playbook(name: str, description: str, category: str, author):
        """
        Create a new playbook.
        
        :param name: Playbook name as str. Example: "React Development"
        :param description: Description as str. Example: "Modern React patterns"
        :param category: Category as str. Example: "development"
        :param author: User instance. Example: User(id=1, username="maria")
        :return: Created Playbook instance. Example: Playbook(id=1, name="React Development")
        :raises ValidationError: If name is empty or duplicate
        """
        if not name or not name.strip():
            raise ValidationError("Playbook name cannot be empty")
        
        if Playbook.objects.filter(name=name, author=author).exists():
            raise ValidationError(f"Playbook '{name}' already exists")
        
        playbook = Playbook.objects.create(
            name=name,
            description=description,
            category=category,
            author=author,
            version=Decimal('0.1'),
            status='draft'
        )
        return playbook
    
    @staticmethod
    def get_user_playbooks(user):
        """
        Get all playbooks for a user.
        
        :param user: User instance. Example: User(id=1)
        :return: QuerySet of Playbooks. Example: <QuerySet [<Playbook: React Dev>]>
        """
        return Playbook.objects.filter(author=user).order_by('-updated_at')
```

### Pattern 3: Repository Pattern (Data Access Abstraction)

Currently using Django ORM directly, but structured to allow swapping:

```python
# methodology/repositories/playbook_repository.py
from ..models import Playbook

class PlaybookRepository:
    """Data access layer for Playbooks."""
    
    def get_by_id(self, playbook_id: int):
        """Get playbook by ID."""
        return Playbook.objects.get(id=playbook_id)
    
    def filter_by_user(self, user):
        """Get all playbooks for user."""
        return Playbook.objects.filter(author=user)
    
    def create(self, **kwargs):
        """Create new playbook."""
        return Playbook.objects.create(**kwargs)
```

### Pattern 4: URL Pattern Registration

Register views in app urls.py with descriptive names:

```python
# methodology/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Playbook URLs
    path('playbooks/', views.playbook_list, name='playbook_list'),
    path('playbooks/create/', views.playbook_create, name='playbook_create'),
    path('playbooks/<int:playbook_id>/', views.playbook_detail, name='playbook_detail'),
    path('playbooks/<int:playbook_id>/edit/', views.playbook_edit, name='playbook_edit'),
    path('playbooks/<int:playbook_id>/delete/', views.playbook_delete, name='playbook_delete'),
]
```

Follow RESTful conventions:
- List: `/resource/`
- Create: `/resource/create/`
- Detail: `/resource/<id>/`
- Edit: `/resource/<id>/edit/`
- Delete: `/resource/<id>/delete/`

### Pattern 5: Testing Django Views

Use Django TestCase (NOT DRF test clients):

```python
# tests/integration/test_playbook_views.py
from django.test import TestCase, Client
from django.contrib.auth.models import User
from methodology.models import Playbook

class PlaybookViewsTest(TestCase):
    """Test playbook views with Django test client."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_playbook_list_returns_correct_template(self):
        """Test playbook list view returns correct template."""
        response = self.client.get('/playbooks/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'playbooks/list.html')
        self.assertIn('playbooks', response.context)
    
    def test_playbook_create_success(self):
        """Test creating playbook via POST."""
        response = self.client.post('/playbooks/create/', {
            'name': 'Test Playbook',
            'description': 'Test description',
            'category': 'test'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(Playbook.objects.filter(name='Test Playbook').exists())
    
    def test_playbook_create_validation_error(self):
        """Test playbook create with invalid data."""
        response = self.client.post('/playbooks/create/', {
            'name': '',  # Empty name
            'description': 'Test',
            'category': 'test'
        })
        
        self.assertEqual(response.status_code, 200)  # Re-render form
        self.assertContains(response, 'error')
        self.assertFalse(Playbook.objects.filter(description='Test').exists())
```

### Pattern 6: Testing with pytest

Use pytest for unit and integration tests:

```python
# tests/unit/test_playbook_service.py
import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from methodology.services.playbook_service import PlaybookService
from methodology.models import Playbook

@pytest.mark.django_db
class TestPlaybookService:
    """Test PlaybookService business logic."""
    
    def test_create_playbook_success(self):
        """Test successful playbook creation."""
        user = User.objects.create_user(username='testuser')
        service = PlaybookService()
        
        playbook = service.create_playbook(
            name='Test Playbook',
            description='Test description',
            category='test',
            author=user
        )
        
        assert playbook.id is not None
        assert playbook.name == 'Test Playbook'
        assert playbook.status == 'draft'
        assert playbook.version == Decimal('0.1')
    
    def test_create_playbook_duplicate_name_raises_error(self):
        """Test creating duplicate playbook raises ValidationError."""
        user = User.objects.create_user(username='testuser')
        service = PlaybookService()
        
        service.create_playbook(
            name='Duplicate',
            description='First',
            category='test',
            author=user
        )
        
        with pytest.raises(ValidationError, match="already exists"):
            service.create_playbook(
                name='Duplicate',
                description='Second',
                category='test',
                author=user
            )
```

### Pattern 7: Model Registration with Admin

Register new models with Django admin for easy data management:

```python
# methodology/admin.py
from django.contrib import admin
from .models import Playbook, Workflow, Activity

@admin.register(Playbook)
class PlaybookAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'status', 'author', 'updated_at')
    list_filter = ('status', 'category')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('name', 'playbook', 'order', 'updated_at')
    list_filter = ('playbook',)
    search_fields = ('name', 'description')
```

## Common Pitfalls

### ❌ Don't: Use DRF test clients for template views
```python
# Wrong - DRF APIClient for template views
from rest_framework.test import APIClient
client = APIClient()
response = client.get('/playbooks/')
```

### ✅ Do: Use Django test client
```python
# Correct - Django Client for template views
from django.test import Client
client = Client()
response = client.get('/playbooks/')
```

### ❌ Don't: Put business logic in views
```python
# Wrong - business logic in view
def create_playbook(request):
    if Playbook.objects.filter(name=request.POST['name']).exists():
        # validation logic in view
        messages.error(request, 'Duplicate name')
        return render(request, 'form.html')
    playbook = Playbook.objects.create(...)  # direct ORM in view
```

### ✅ Do: Use service layer
```python
# Correct - delegate to service
def create_playbook(request):
    service = PlaybookService()
    try:
        playbook = service.create_playbook(...)  # service handles logic
        messages.success(request, 'Created')
        return redirect('detail', playbook.id)
    except ValidationError as e:
        messages.error(request, str(e))
        return render(request, 'form.html')
```

### ❌ Don't: Mix sync and async incorrectly
```python
# Wrong - async view with sync ORM
async def playbook_list(request):
    playbooks = Playbook.objects.all()  # SynchronousOnlyOperation error
```

### ✅ Do: Keep views sync or use sync_to_async
```python
# Correct - sync view with sync ORM
def playbook_list(request):
    playbooks = Playbook.objects.all()  # Works fine

# Or use sync_to_async wrapper
from asgiref.sync import sync_to_async

async def playbook_list(request):
    playbooks = await sync_to_async(list)(Playbook.objects.all())
```

## Quality Gates

Before declaring backend implementation complete:

- [ ] All views properly registered in `urls.py` with descriptive names
- [ ] Services layer properly structured (business logic separate from views)
- [ ] Repository pattern used for data access (or direct ORM with clear separation)
- [ ] All models registered with Django admin
- [ ] Views return HTML templates (not JSON) unless building API
- [ ] Template context always validated and documented
- [ ] Unit tests written with pytest for services
- [ ] Integration tests written with Django TestCase for views
- [ ] All tests use real database (no mocking in integration tests)
- [ ] 100% test pass rate
- [ ] URL patterns follow RESTful conventions
- [ ] Business logic reusable between MCP and Web UI

## Testing Strategy

### Unit Tests (pytest)
- Test services in isolation
- Test model methods
- Test utility functions
- Fast (<1s per test)

### Integration Tests (Django TestCase)
- Test views with Django test client
- Test complete workflows
- Test database state changes
- Use real database, no mocking
- Fast (<5s per test class)

### Test Organization
```
tests/
├── unit/
│   ├── test_playbook_service.py
│   ├── test_workflow_service.py
│   └── test_activity_service.py
├── integration/
│   ├── test_playbook_views.py
│   ├── test_workflow_views.py
│   └── test_activity_views.py
└── conftest.py
```
