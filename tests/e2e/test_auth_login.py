"""E2E tests for user authentication - Login flow.

These tests use Playwright in SYNC mode to test the login functionality
from a real browser perspective, ensuring the full stack works correctly.

IMPORTANT: These tests run in SYNC mode (not async) to avoid
pytest-asyncio conflicts with Django ORM operations.

MCP integration tests use ``django_db(transaction=True)``, which flushes the DB
between tests and removes the ``admin`` user from session ``e2e_seed`` loaddata.
Re-seed credentials before the happy-path login so a full ``pytest tests/ tests/e2e/`` run stays green.
"""
import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import Page

User = get_user_model()


@pytest.fixture
def admin_login_user(db):
    """Ensure admin / admin123 exists after TransactionTestCase-style integration tests."""
    user, _ = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'is_staff': True,
            'is_superuser': True,
        },
    )
    user.email = 'admin@example.com'
    user.is_staff = True
    user.is_superuser = True
    user.set_password('admin123')
    user.save()
    return user


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestLoginE2E:
    """End-to-end tests for user login using Playwright."""
    
    def test_login_with_valid_credentials_success(self, page: Page, live_server_url: str, admin_login_user):
        """
        Test E2E-AUTH-01: User can log in with valid credentials.
        
        Given: User 'admin' exists with password 'admin123'
        When: User navigates to login page and enters valid credentials
        Then: User is redirected to dashboard and sees welcome message
        """
        # Navigate to login page
        page.goto(f"{live_server_url}/auth/user/login/")
        
        # Verify we're on the login page
        assert "Login" in page.title()
        
        # Fill in login form
        page.fill('input[name="username"]', 'admin')
        page.fill('input[name="password"]', 'admin123')
        
        # Submit the form
        page.click('button[type="submit"]')
        
        # Wait for navigation to complete
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_function(
            "() => !window.location.pathname.includes('/auth/user/login')",
            timeout=10_000,
        )
        
        # Verify successful login - should be on dashboard or redirected
        assert page.url.startswith(live_server_url)
        # Check that we're not on the login page anymore
        assert '/auth/user/login/' not in page.url
    
    def test_login_with_invalid_credentials_shows_error(self, page: Page, live_server_url: str):
        """
        Test E2E-AUTH-02: Login with invalid credentials shows error.
        
        Given: User is on login page
        When: User enters invalid credentials
        Then: Error message is displayed and user stays on login page
        """
        # Navigate to login page
        page.goto(f"{live_server_url}/auth/user/login/")
        
        # Fill in login form with invalid credentials
        page.fill('input[name="username"]', 'invalid_user')
        page.fill('input[name="password"]', 'wrongpassword')
        
        # Submit the form
        page.click('button[type="submit"]')
        
        # Wait for page to reload/respond
        page.wait_for_load_state('domcontentloaded')
        
        # Verify we're still on the login page
        assert '/auth/user/login/' in page.url
        
        # Verify error message appears (check for common error indicators)
        content = page.content()
        assert any(text in content.lower() for text in ['error', 'invalid', 'incorrect', 'wrong'])
    
    def test_login_page_displays_form(self, page: Page, live_server_url: str):
        """
        Test E2E-AUTH-03: Login page displays login form correctly.
        
        Given: User is on login page
        Then: Login form with username and password fields is visible
        """
        # Navigate to login page
        page.goto(f"{live_server_url}/auth/user/login/")
        
        # Verify form elements are present
        assert page.locator('input[name="username"]').is_visible()
        assert page.locator('input[name="password"]').is_visible()
        assert page.locator('button[type="submit"]').is_visible()
