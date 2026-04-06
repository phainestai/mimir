# Skill: pytest Fixture Management for E2E Tests

**Capability Domain**: TEST_DATA
**Technology Stack**: pytest+Django

## Overview

Patterns for managing test data and fixtures in E2E tests, including fixture files, data seeding, and test isolation strategies.

## Reference Implementation

### Pattern 1: JSON Fixture Files

```json
// tests/fixtures/e2e_seed.json
[
  {
    "model": "auth.user",
    "pk": 1,
    "fields": {
      "username": "admin",
      "email": "admin@example.com",
      "is_staff": true,
      "is_superuser": true
    }
  },
  {
    "model": "methodology.playbook",
    "pk": 1,
    "fields": {
      "name": "FeatureFactory",
      "description": "Complete feature development methodology",
      "category": "development",
      "version": "3.8",
      "status": "released",
      "author": 1
    }
  },
  {
    "model": "methodology.workflow",
    "pk": 1,
    "fields": {
      "name": "Build Feature",
      "description": "Complete workflow for building features",
      "playbook": 1,
      "order": 1
    }
  }
]
```

### Pattern 2: Loading Fixtures in Tests

```python
# tests/e2e/conftest.py
import pytest
from django.core.management import call_command

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Load E2E test fixtures once per session."""
    with django_db_blocker.unblock():
        call_command('loaddata', 'tests/fixtures/e2e_seed.json')

@pytest.fixture
def e2e_data(db):
    """Ensure E2E data is available for each test."""
    # Data already loaded by django_db_setup
    # This fixture just ensures db is available
    pass
```

### Pattern 3: Factory-Based Fixtures

```python
# tests/conftest.py
import pytest
from django.contrib.auth.models import User
from methodology.models import Playbook, Workflow, Activity

@pytest.fixture
def user_factory(db):
    """Factory for creating test users."""
    def create_user(username='testuser', **kwargs):
        defaults = {
            'email': f'{username}@example.com',
            'is_active': True
        }
        defaults.update(kwargs)
        return User.objects.create_user(username=username, **defaults)
    return create_user

@pytest.fixture
def playbook_factory(db, user_factory):
    """Factory for creating test playbooks."""
    def create_playbook(name='Test Playbook', author=None, **kwargs):
        if author is None:
            author = user_factory()
        
        defaults = {
            'description': 'Test description',
            'category': 'test',
            'version': '0.1',
            'status': 'draft'
        }
        defaults.update(kwargs)
        
        return Playbook.objects.create(
            name=name,
            author=author,
            **defaults
        )
    return create_playbook

@pytest.fixture
def workflow_factory(db, playbook_factory):
    """Factory for creating test workflows."""
    def create_workflow(name='Test Workflow', playbook=None, **kwargs):
        if playbook is None:
            playbook = playbook_factory()
        
        defaults = {
            'description': 'Test workflow',
            'order': 1
        }
        defaults.update(kwargs)
        
        return Workflow.objects.create(
            name=name,
            playbook=playbook,
            **defaults
        )
    return create_workflow
```

### Pattern 4: Using Factories in Tests

```python
# tests/integration/test_playbook_crud.py
import pytest

@pytest.mark.django_db
class TestPlaybookCRUD:
    """Test playbook CRUD operations."""
    
    def test_create_playbook(self, user_factory, playbook_factory):
        """Test creating a playbook."""
        user = user_factory(username='maria')
        playbook = playbook_factory(
            name='React Development',
            author=user,
            category='development'
        )
        
        assert playbook.id is not None
        assert playbook.name == 'React Development'
        assert playbook.author == user
    
    def test_list_user_playbooks(self, user_factory, playbook_factory):
        """Test listing playbooks for a user."""
        user1 = user_factory(username='maria')
        user2 = user_factory(username='john')
        
        playbook1 = playbook_factory(name='P1', author=user1)
        playbook2 = playbook_factory(name='P2', author=user1)
        playbook3 = playbook_factory(name='P3', author=user2)
        
        user1_playbooks = Playbook.objects.filter(author=user1)
        
        assert user1_playbooks.count() == 2
        assert playbook1 in user1_playbooks
        assert playbook2 in user1_playbooks
        assert playbook3 not in user1_playbooks
```

### Pattern 5: Test Isolation with Transaction Rollback

```python
# tests/conftest.py
import pytest

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests automatically."""
    pass

# Each test runs in a transaction that's rolled back
# No need for manual cleanup
```

### Pattern 6: Management Command for Seeding

```python
# methodology/management/commands/seed_test_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from methodology.models import Playbook, Workflow, Activity

class Command(BaseCommand):
    help = 'Seed database with test data for E2E tests'
    
    def handle(self, *args, **options):
        """Create test data."""
        self.stdout.write('Seeding test data...')
        
        # Create test user
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(f'Created user: {user.username}')
        
        # Create test playbook
        playbook, created = Playbook.objects.get_or_create(
            name='FeatureFactory',
            author=user,
            defaults={
                'description': 'Complete feature development methodology',
                'category': 'development',
                'version': '3.8',
                'status': 'released'
            }
        )
        if created:
            self.stdout.write(f'Created playbook: {playbook.name}')
        
        # Create test workflow
        workflow, created = Workflow.objects.get_or_create(
            name='Build Feature',
            playbook=playbook,
            defaults={
                'description': 'Complete workflow for building features',
                'order': 1
            }
        )
        if created:
            self.stdout.write(f'Created workflow: {workflow.name}')
        
        self.stdout.write(self.style.SUCCESS('Test data seeded successfully'))
```

## Common Pitfalls

### ❌ Don't: Create fixtures manually in each test
```python
# Wrong - repetitive setup
def test_playbook_create():
    user = User.objects.create_user(username='test')
    playbook = Playbook.objects.create(name='Test', author=user)
    # ... test logic ...

def test_playbook_update():
    user = User.objects.create_user(username='test')  # Duplicate
    playbook = Playbook.objects.create(name='Test', author=user)  # Duplicate
    # ... test logic ...
```

### ✅ Do: Use factory fixtures
```python
# Correct - reusable factories
def test_playbook_create(user_factory, playbook_factory):
    user = user_factory()
    playbook = playbook_factory(author=user)
    # ... test logic ...

def test_playbook_update(user_factory, playbook_factory):
    user = user_factory()
    playbook = playbook_factory(author=user)
    # ... test logic ...
```

### ❌ Don't: Share mutable data between tests
```python
# Wrong - shared state
TEST_USER = User.objects.create_user(username='test')

def test_1():
    TEST_USER.email = 'new@example.com'  # Mutates shared state
    TEST_USER.save()

def test_2():
    assert TEST_USER.email == 'test@example.com'  # Fails!
```

### ✅ Do: Create fresh data per test
```python
# Correct - isolated data
@pytest.fixture
def test_user(db):
    return User.objects.create_user(username='test')

def test_1(test_user):
    test_user.email = 'new@example.com'
    test_user.save()
    # Changes rolled back after test

def test_2(test_user):
    assert test_user.email == 'test@example.com'  # Passes!
```

## Quality Gates

- [ ] Fixture files created in `tests/fixtures/`
- [ ] Factory fixtures defined in `conftest.py`
- [ ] Management command for seeding test data
- [ ] Test isolation via transaction rollback
- [ ] No shared mutable state between tests
- [ ] Fixtures scoped appropriately (function/class/session)
- [ ] All tests use fixtures (no manual data creation)
- [ ] Fixture data realistic and comprehensive

## Fixture Organization

```
tests/
├── fixtures/
│   ├── e2e_seed.json           # E2E test data
│   ├── journey_seed.json       # Journey test data
│   └── playbooks_seed.json     # Playbook-specific data
├── conftest.py                  # Shared fixtures
└── e2e/
    └── conftest.py              # E2E-specific fixtures
```

## Fixture Scopes

- **function** (default): New instance per test function
- **class**: Shared across test class methods
- **module**: Shared across test module
- **session**: Created once per test session

```python
@pytest.fixture(scope='function')  # New per test
def test_user(db):
    return User.objects.create_user(username='test')

@pytest.fixture(scope='session')  # Once per session
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('loaddata', 'e2e_seed.json')
```

## Best Practices

1. **Use factories for dynamic data**: User factories, playbook factories
2. **Use JSON fixtures for static data**: Seed data, reference data
3. **Scope fixtures appropriately**: Function for isolation, session for performance
4. **Name fixtures descriptively**: `authenticated_client`, `draft_playbook`
5. **Document fixture purpose**: Docstrings explaining what fixture provides
6. **Keep fixtures DRY**: Compose fixtures from other fixtures
7. **Isolate tests**: Each test gets fresh data via transaction rollback
