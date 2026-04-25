"""User Journey Certification Test for FOB-PLAYBOOKS-EDIT_PLAYBOOK-25.

Scenario: Edit form renders for playbook with no tags.
"""
import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import expect

from methodology.models import Playbook

User = get_user_model()


@pytest.fixture
def no_tags_playbook(transactional_db):
    """A playbook with no tags owned by a test user."""
    user = User.objects.create_user(
        username='journey_edit_user',
        password='testpass123',
    )
    playbook = Playbook.objects.create(
        name='Tagless Playbook',
        description='A playbook with no tags assigned',
        category='development',
        author=user,
        tags=[],
    )
    return {'user': user, 'playbook': playbook}


@pytest.mark.e2e
def test_edit_form_renders_for_playbook_with_no_tags(page, live_server, no_tags_playbook):
    """EDIT_PLAYBOOK-25: Edit form opens without errors for a tagless playbook."""
    user = no_tags_playbook['user']
    playbook = no_tags_playbook['playbook']

    # Login
    page.goto(f'{live_server.url}/auth/user/login/')
    page.get_by_test_id('login-username-input').fill(user.username)
    page.get_by_test_id('login-password-input').fill('testpass123')
    page.get_by_test_id('login-submit-button').click()
    expect(page).to_have_url(f'{live_server.url}/dashboard/')

    # Navigate to edit form
    page.goto(f'{live_server.url}/playbooks/{playbook.pk}/edit/')
    expect(page).to_have_url(f'{live_server.url}/playbooks/{playbook.pk}/edit/')

    # Form renders without error — tags field is empty
    tags_input = page.get_by_test_id('playbook-tags-input')
    expect(tags_input).to_be_visible()
    expect(tags_input).to_have_value('')

    # Add tags and save
    tags_input.fill('ux, research')
    page.get_by_test_id('save-button').click()

    # Redirected to detail page after save
    expect(page).to_have_url(f'{live_server.url}/playbooks/{playbook.pk}/')

    # Reopen edit form — tags are persisted and pre-filled
    page.goto(f'{live_server.url}/playbooks/{playbook.pk}/edit/')
    expect(page).to_have_url(f'{live_server.url}/playbooks/{playbook.pk}/edit/')
    expect(page.get_by_test_id('playbook-tags-input')).to_have_value('ux, research')
