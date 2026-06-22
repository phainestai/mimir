"""
E2E tests for Content Browser URL management.

Covers playbook switch via pushState (FOB-CONTENT-BROWSER-03b).
Type/phase filter URL scenarios removed — filter toolbar UI was dropped (Phase B4 Option A).

Run: pytest tests/e2e/test_content_browser_url.py -x
"""

import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from e2e_helpers import login
from methodology.models import Activity, Playbook, Workflow

User = get_user_model()

# FOB-63 defaults persisted in URL via _filtersToQueryString after init.
_FOB63_QS = '?layout=klay&routing=straight&compound=workflow-activity'


@pytest.fixture
def two_playbooks(transactional_db):
    """Two accessible playbooks for playbook-switch URL tests."""
    user = User.objects.create_user(
        username='url_user_two', email='url_two@test.com', password='testpass123',
    )
    mark_email_verified(user)
    pb1 = Playbook.objects.create(
        name='Playbook Alpha', description='', category='development',
        author=user, visibility='public', status='released',
    )
    wf1 = Workflow.objects.create(playbook=pb1, name='Alpha WF', order=1)
    Activity.objects.create(workflow=wf1, name='Alpha Act', order=1)
    pb2 = Playbook.objects.create(
        name='Playbook Beta', description='', category='development',
        author=user, visibility='public', status='released',
    )
    wf2 = Workflow.objects.create(playbook=pb2, name='Beta WF', order=1)
    Activity.objects.create(workflow=wf2, name='Beta Act', order=1)
    return {'username': 'url_user_two', 'password': 'testpass123', 'pb1': pb1, 'pb2': pb2}


@pytest.mark.django_db(transaction=True)
class TestURLManagement:
    """S3 — Client-side URL management (pushState)."""

    def test_playbook_switch_updates_url_via_push_state(self, page: Page, live_server_url, two_playbooks):
        """Switching playbook updates URL to /browser/<new_pk>/ via pushState."""
        login(page, live_server_url, two_playbooks['username'], two_playbooks['password'])
        pk1 = two_playbooks['pb1'].pk
        pk2 = two_playbooks['pb2'].pk
        page.goto(f"{live_server_url}/browser/{pk1}/")
        page.wait_for_function("() => typeof _pushPlaybookUrl === 'function'", timeout=10_000)

        page.evaluate(f"_pushPlaybookUrl({pk2}, {{types: [], phases: []}})")

        expect(page).to_have_url(f"{live_server_url}/browser/{pk2}/{_FOB63_QS}")

    def test_back_button_returns_to_previous_playbook(self, page: Page, live_server_url, two_playbooks):
        """Browser back button after playbook switch returns to previous /browser/<pk>/."""
        login(page, live_server_url, two_playbooks['username'], two_playbooks['password'])
        pk1 = two_playbooks['pb1'].pk
        pk2 = two_playbooks['pb2'].pk
        page.goto(f"{live_server_url}/browser/{pk1}/")
        page.wait_for_function("() => typeof _pushPlaybookUrl === 'function'", timeout=10_000)

        page.evaluate(f"_pushPlaybookUrl({pk2}, {{types: [], phases: []}})")
        expect(page).to_have_url(f"{live_server_url}/browser/{pk2}/{_FOB63_QS}")

        page.go_back()
        expect(page).to_have_url(f"{live_server_url}/browser/{pk1}/{_FOB63_QS}")
