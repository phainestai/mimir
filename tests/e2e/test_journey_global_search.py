"""User Journey Certification Test for NAV-06 Global Search."""
import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_complete_global_search_journey(page, live_server, nav06_sample_data):
    """Test complete global search journey with HTMX."""
    # Login
    page.goto(f'{live_server.url}/auth/user/login/')
    page.get_by_test_id('login-username-input').fill(nav06_sample_data['username'])
    page.get_by_test_id('login-password-input').fill(nav06_sample_data['password'])
    page.get_by_test_id('login-submit-button').click()
    expect(page).to_have_url(f'{live_server.url}/dashboard/')
    
    # Verify navbar search visible
    search_input = page.get_by_test_id('global-search-input')
    expect(search_input).to_be_visible()
    
    # Type in search
    search_input.fill('Component')
    page.wait_for_timeout(500)
    
    # Verify suggestions appear
    suggestions = page.locator('#global-search-suggestions-container')
    expect(suggestions).to_be_visible()
    
    # Submit search
    search_input.press('Enter')
    expect(page).to_have_url(f'{live_server.url}/search/?q=Component')
    
    # Verify results
    expect(page.locator('body')).to_contain_text(nav06_sample_data['playbook_name'])


@pytest.mark.e2e
def test_anonymous_user_no_search(page, live_server):
    """Test anonymous user cannot see search."""
    page.goto(f'{live_server.url}/')
    search_form = page.locator('[data-testid="global-search-form"]')
    expect(search_form).not_to_be_visible()
