# E2E Test Setup - Playwright with Django

## Problem

Playwright's sync API (`sync_playwright()`) internally creates an asyncio event loop, which conflicts with Django's requirement for synchronous context during test setup and teardown, causing `SynchronousOnlyOperation` errors.

## Solution

This solution implements Playwright E2E tests that run completely isolated from the main test suite:

1. **Separate pytest configuration** - E2E tests have their own `pytest.ini` that disables pytest-asyncio and pytest-playwright plugins
2. **Environment variable workaround** - Uses `DJANGO_ALLOW_ASYNC_UNSAFE=true` to allow Django operations within Playwright's event loop
3. **Isolated test execution** - E2E tests run separately from unit/integration tests

### Key Components

#### 1. Main Pytest Configuration (`pytest.ini`)

```ini
addopts = 
    --ignore=tests/e2e                           # Exclude E2E tests from main test suite
asyncio_mode = auto                              # Only treat tests marked with @pytest.mark.asyncio as async
```

**Why:**
- Excludes E2E tests so they don't interfere with unit/integration tests
- Allows async integration tests (MCP tools) to continue working

#### 2. E2E Pytest Configuration (`tests/e2e/pytest.ini`)

```ini
addopts = 
    -p no:playwright                             # Disable pytest-playwright plugin
    -p no:asyncio                                # Disable pytest-asyncio plugin
    -p no:anyio                                  # Disable anyio plugin
```

**Why:**
- Prevents plugins from creating additional async context
- Runs E2E tests in isolated environment

#### 3. E2E Test Configuration (`tests/e2e/conftest.py`)

```python
import os
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'  # Allow Django in async context

@pytest.fixture(scope="module")
def playwright():
    with sync_playwright() as p:
        yield p
```

**Why:**
- `DJANGO_ALLOW_ASYNC_UNSAFE` allows Django ORM calls within Playwright's event loop
- Manual fixture creation gives full control over initialization

#### 4. E2E Tests (e.g., `tests/e2e/test_auth_login.py`)

Tests use standard synchronous Python:

```python
@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestLoginE2E:
    def test_login_with_valid_credentials_success(self, page: Page, live_server_url: str):
        page.goto(f"{live_server_url}/auth/user/login/")
        page.fill('input[name="username"]', 'admin')
        page.click('button[type="submit"]')
```

**Why:**
- No `async def` or `await` syntax needed
- Uses Django's `live_server` fixture for real server testing

## Test Results

Running tests separately achieves 100% pass rate:

### Unit and Integration Tests

```bash
pytest tests/
```

**Results:**
- ✅ 263 tests PASSED
- ⏭️  2 tests SKIPPED
- ❌ 0 ERRORS

### E2E Tests

```bash
cd tests/e2e && pytest .
```

**Results:**
- ✅ 4 tests PASSED
- ❌ 0 ERRORS

### Total: 267 tests PASSED, 0 ERRORS ✅

## Usage

### Running E2E Tests Only

```bash
pytest tests/e2e/ -v
```

### Running Without E2E Tests

```bash
pytest tests/ -m "not e2e"
```

### Running Full Suite

```bash
pytest tests/
```

## Writing New E2E Tests

1. **Use sync API only** — no `async def` or `await`
2. **Mark tests** — use `@pytest.mark.e2e` and `@pytest.mark.django_db(transaction=True)` where DB isolation is required
3. **Use fixtures** — `page`, `live_server_url` are available
4. **Use shared helpers** — import from `e2e_helpers` (`login`, `wait_for_cy_graph`, `open_content_browser`); do not copy `_login()` per file
5. **Follow pattern** — see `tests/e2e/test_content_browser_graph.py` (migrated) and `tests/e2e/test_auth_login.py`

### Fixture scopes (Act-16 A0)

| Fixture | Default scope | Override |
|---------|---------------|----------|
| `live_server` | **session** (one WSGI thread per e2e run) | `E2E_LIVE_SERVER_SCOPE=function` when mixing `pytest tests/` + `tests/e2e/` |
| `browser` | module | — |
| `page` / `context` | function (isolated cookies) | — |

Signed-cookie sessions (`mimir.settings.e2e`) avoid SQLite session races that motivated per-test servers.

### Commands

```bash
# Representative checkpoint (fast)
pytest tests/e2e/test_auth_login.py tests/e2e/test_content_browser_graph.py -q --durations=10

# Full content-browser batch (phase gates only)
pytest tests/e2e/test_content_browser*.py -q --durations=20 2>&1 | tee tests.log

# Mixing unit/integration + e2e in one run
E2E_LIVE_SERVER_SCOPE=function pytest tests/ tests/e2e/
```

### Wait strategy

Prefer `domcontentloaded` + `wait_for_cy_graph()` / Playwright `expect()` — **not** `networkidle`. Avoid `wait_for_timeout` except documented animation settles.

Example:

```python
from e2e_helpers import login, open_content_browser

def test_something(page, live_server_url, my_playbook):
    login(page, live_server_url, user, password)
    open_content_browser(page, live_server_url, my_playbook.pk)
    assert page.get_by_test_id('browser-canvas').is_visible()
```

## Key Principles

1. **Isolation** - E2E tests don't interfere with unit/integration tests
2. **Sync Mode** - All E2E tests run in synchronous mode
3. **Real Server** - Uses Django's live server for authentic testing
4. **Proper Cleanup** - Playwright fixtures handle browser cleanup
5. **Fixture Loading** - Test data loaded once per session

## References

- [Playwright Python Sync API](https://playwright.dev/python/docs/api/class-playwright)
- [pytest-django live_server](https://pytest-django.readthedocs.io/en/latest/helpers.html#live-server)
- [pytest-asyncio modes](https://pytest-asyncio.readthedocs.io/en/latest/concepts.html#modes)
