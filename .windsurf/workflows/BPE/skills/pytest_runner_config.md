# Skill: pytest Runner Configuration

**Capability Domain**: TEST_FRAMEWORK
**Technology Stack**: pytest

## Overview

Configuration patterns for pytest test runner, including pytest.ini setup, command-line options, markers, and test discovery patterns.

## Reference Implementation

### Pattern 1: pytest.ini Configuration

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = mimir.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
testpaths = tests

addopts = 
    -v
    --strict-markers
    --tb=short
    --disable-warnings
    -p no:warnings
    --log-cli-level=INFO
    --log-file=tests.log
    --log-file-level=INFO
    --log-file-format=%(asctime)s [%(levelname)s] %(message)s
    --log-file-date-format=%Y-%m-%d %H:%M:%S
    --cov-report=term-missing
    --cov-report=html

markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (real dependencies)
    e2e: End-to-end tests (full user journeys)
    slow: Slow running tests
    django_db: Tests that require database access
```

### Pattern 2: Running Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_playbook_service.py

# Run specific test class
pytest tests/unit/test_playbook_service.py::TestPlaybookService

# Run specific test method
pytest tests/unit/test_playbook_service.py::TestPlaybookService::test_create_playbook

# Run with coverage
pytest tests/ --cov=methodology --cov-report=html

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run all except slow tests
pytest -m "not slow"

# Run with specific log level
pytest tests/ --log-cli-level=DEBUG

# Stop on first failure
pytest tests/ -x

# Run last failed tests
pytest tests/ --lf

# Run failed tests first, then others
pytest tests/ --ff

# Run tests in parallel (requires pytest-xdist)
pytest tests/ -n auto
```

### Pattern 3: Test Discovery

```python
# tests/conftest.py
import pytest
from django.contrib.auth.models import User

@pytest.fixture(scope='session')
def django_db_setup():
    """Configure test database."""
    pass

@pytest.fixture
def test_user(db):
    """Create test user."""
    return User.objects.create_user(
        username='testuser',
        password='testpass123'
    )

@pytest.fixture
def authenticated_client(client, test_user):
    """Create authenticated test client."""
    client.login(username='testuser', password='testpass123')
    return client
```

### Pattern 4: Makefile Targets

```makefile
# Makefile
.PHONY: test test-unit test-integration test-e2e test-cov

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v -m unit

test-integration:
	pytest tests/integration/ -v -m integration

test-e2e:
	pytest tests/e2e/ -v -m e2e

test-cov:
	pytest tests/ --cov=methodology --cov-report=html --cov-report=term

test-watch:
	python continuous_test_runner.py

test-failed:
	pytest tests/ --lf -v
```

## Common Pitfalls

### ❌ Don't: Run tests without configuration
```bash
# Wrong - no pytest.ini
pytest
```

### ✅ Do: Use pytest.ini for consistent configuration
```ini
# Correct - pytest.ini with settings
[pytest]
testpaths = tests
addopts = -v --tb=short
```

### ❌ Don't: Mix test discovery patterns
```python
# Wrong - inconsistent naming
def check_playbook():  # Won't be discovered
class PlaybookTests:   # Won't be discovered
```

### ✅ Do: Follow pytest conventions
```python
# Correct - pytest discovers these
def test_playbook():
class TestPlaybook:
```

## Quality Gates

- [ ] pytest.ini exists with proper configuration
- [ ] Test discovery patterns configured
- [ ] Markers defined for test categories
- [ ] Logging configured (file and console)
- [ ] Coverage reporting configured
- [ ] Makefile targets created for common operations
- [ ] All tests discoverable by pytest
- [ ] Tests organized in proper directory structure

## Test Organization

```
tests/
├── unit/                    # pytest -m unit
├── integration/             # pytest -m integration
├── e2e/                     # pytest -m e2e
├── conftest.py              # Shared fixtures
└── pytest.ini               # Configuration
```

## Recommended pytest Plugins

```txt
# requirements.txt
pytest>=8.0.0
pytest-django>=4.5.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
pytest-xdist>=3.3.0         # Parallel execution
pytest-timeout>=2.1.0       # Test timeouts
pytest-mock>=3.11.0         # Mocking support
```
