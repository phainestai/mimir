"""E2E test configuration with Playwright and Django live server.

IMPORTANT: Playwright's sync API creates an event loop internally, which conflicts
with Django's requirement for synchronous context. To work around this, we use
lazy initialization - Playwright is only started when first accessed in a test,
after Django setup is complete.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Generator

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright
from pytest_django import live_server_helper
from pytest_django.lazy_django import skip_if_no_django

from e2e_helpers import LOGIN_URL_PATH, login, open_content_browser, wait_for_cy_edges, wait_for_cy_graph

logger = logging.getLogger(__name__)

# Allow Django to run in async context for E2E tests only
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'

# Re-export helpers for tests: from e2e_helpers import login, ...
__all__ = [
    'LOGIN_URL_PATH',
    'login',
    'open_content_browser',
    'wait_for_cy_graph',
    'wait_for_cy_edges',
]


def e2e_live_server_scope() -> str:
    """Return live_server fixture scope: session (default) or function."""
    return os.getenv('E2E_LIVE_SERVER_SCOPE', 'session').lower()


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Load E2E test fixtures at session start.

    This fixture extends the base django_db_setup to load
    test data needed for E2E scenarios.
    """
    from django.core.management import call_command

    fixture_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../fixtures/e2e_seed.json')
    )

    with django_db_blocker.unblock():
        call_command('loaddata', fixture_path)


class LazyPlaywright:
    """Lazy wrapper for Playwright to delay event loop creation."""

    def __init__(self):
        self._playwright = None
        self._context_manager = None

    def __enter__(self):
        self._context_manager = sync_playwright()
        self._playwright = self._context_manager.__enter__()
        return self._playwright

    def __exit__(self, *args):
        if self._context_manager:
            return self._context_manager.__exit__(*args)


@pytest.fixture(scope="module")
def playwright():
    """Create Playwright instance for the test module."""
    lazy_pw = LazyPlaywright()
    with lazy_pw as p:
        yield p


@pytest.fixture(scope="module")
def browser(playwright):
    """Launch Chromium in headless mode for the test module."""
    browser = playwright.chromium.launch(headless=True)
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser):
    """Fresh browser context per test (isolated cookies/storage)."""
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        ignore_https_errors=True,
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext):
    """Fresh page per test."""
    page = context.new_page()
    yield page
    page.close()


def _live_server_addr(request: pytest.FixtureRequest) -> str:
    return (
        request.config.getvalue("liveserver")
        or os.getenv("DJANGO_LIVE_TEST_SERVER_ADDRESS")
        or "localhost"
    )


@pytest.fixture(scope="session")
def _live_server_session(
    request: pytest.FixtureRequest,
) -> Generator[live_server_helper.LiveServer, None, None]:
    """One Django live server for the entire e2e session (signed-cookie sessions)."""
    skip_if_no_django()
    addr = _live_server_addr(request)
    logger.info('E2E starting session-scoped live_server at %s', addr)
    server = live_server_helper.LiveServer(addr)
    yield server
    server.stop()


@pytest.fixture(scope="function")
def _live_server_function(
    request: pytest.FixtureRequest,
) -> Generator[live_server_helper.LiveServer, None, None]:
    """Per-test live server — use when mixing e2e with integration tests."""
    skip_if_no_django()
    addr = _live_server_addr(request)
    logger.info('E2E starting function-scoped live_server at %s', addr)
    server = live_server_helper.LiveServer(addr)
    yield server
    server.stop()


@pytest.fixture(scope="function")
def live_server(
    request: pytest.FixtureRequest,
) -> Generator[live_server_helper.LiveServer, None, None]:
    """Django live server — session-scoped by default; set E2E_LIVE_SERVER_SCOPE=function to override."""
    if e2e_live_server_scope() == 'function':
        yield from request.getfixturevalue('_live_server_function')
    else:
        yield request.getfixturevalue('_live_server_session')


@pytest.fixture(scope="function")
def live_server_url(live_server):
    """Base URL for the active live server."""
    return live_server.url
