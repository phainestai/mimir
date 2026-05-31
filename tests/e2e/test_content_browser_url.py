"""
E2E tests for Content Browser URL management.

Tests scenarios from docs/features/act-16-content-browser/01-access-and-nav.feature:
  FOB-CONTENT-BROWSER-03b — URL is the source of truth for active playbook and filters
  FOB-CONTENT-BROWSER-03f — URL filter params are normalised on load

Requires: Playwright, a running dev server, and a seeded database.
Run: pytest tests/e2e/test_content_browser_url.py -x
"""

import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from methodology.models import Phase, Playbook

User = get_user_model()

LOGIN_URL_PATH = '/auth/user/login/'


def _login(page, live_server_url, username, password):
    """Helper: log in via the Playwright page, following established E2E auth pattern."""
    page.goto(f"{live_server_url}{LOGIN_URL_PATH}")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    assert LOGIN_URL_PATH not in page.url, f"Login failed; still on login page. URL: {page.url}"


@pytest.fixture
def two_playbooks(transactional_db):
    """Two accessible playbooks for playbook-switch URL tests."""
    user = User.objects.create_user(
        username='url_user_two', email='url_two@test.com', password='testpass123',
    )
    mark_email_verified(user)
    pb1 = Playbook.objects.create(
        name='Playbook Alpha', description='', category='development',
        author=user, visibility='public',
    )
    pb1.status = 'released'
    pb1.save()
    pb2 = Playbook.objects.create(
        name='Playbook Beta', description='', category='development',
        author=user, visibility='public',
    )
    pb2.status = 'released'
    pb2.save()
    return {'username': 'url_user_two', 'password': 'testpass123', 'pb1': pb1, 'pb2': pb2}


@pytest.fixture
def playbook_with_phases(transactional_db):
    """Playbook with two named phases for filter URL tests."""
    user = User.objects.create_user(
        username='url_user_phases', email='url_phases@test.com', password='testpass123',
    )
    mark_email_verified(user)
    pb = Playbook.objects.create(
        name='Phased Playbook', description='', category='development',
        author=user, visibility='public',
    )
    pb.status = 'released'
    pb.save()
    phase1 = Phase.objects.create(playbook=pb, name='Planning', order=1)
    phase2 = Phase.objects.create(playbook=pb, name='Execution', order=2)
    return {
        'username': 'url_user_phases', 'password': 'testpass123',
        'pb': pb, 'phase1': phase1, 'phase2': phase2,
    }


@pytest.fixture
def seeded_playbook(transactional_db):
    """Playbook with a known phase for param normalisation tests."""
    user = User.objects.create_user(
        username='url_user_seed', email='url_seed@test.com', password='testpass123',
    )
    mark_email_verified(user)
    pb = Playbook.objects.create(
        name='Seed Playbook', description='', category='development',
        author=user, visibility='public',
    )
    pb.status = 'released'
    pb.save()
    phase = Phase.objects.create(playbook=pb, name='Construction', order=1)
    return {
        'username': 'url_user_seed', 'password': 'testpass123',
        'pb': pb, 'phase': phase,
    }


@pytest.mark.django_db(transaction=True)
class TestURLManagement:
    """S3 — Client-side URL management (pushState + param normalisation)."""

    # FOB-CONTENT-BROWSER-03b
    def test_playbook_switch_updates_url_via_push_state(self, page: Page, live_server_url, two_playbooks):
        """Switching playbook updates URL to /browser/<new_pk>/ via pushState."""
        _login(page, live_server_url, two_playbooks['username'], two_playbooks['password'])
        pk1 = two_playbooks['pb1'].pk
        pk2 = two_playbooks['pb2'].pk
        page.goto(f"{live_server_url}/browser/{pk1}/")
        page.wait_for_load_state('domcontentloaded')

        page.evaluate(f"_pushPlaybookUrl({pk2}, {{types: [], phases: []}})")

        expect(page).to_have_url(f"{live_server_url}/browser/{pk2}/")

    # FOB-CONTENT-BROWSER-03b
    def test_back_button_returns_to_previous_playbook(self, page: Page, live_server_url, two_playbooks):
        """Browser back button after playbook switch returns to previous /browser/<pk>/."""
        _login(page, live_server_url, two_playbooks['username'], two_playbooks['password'])
        pk1 = two_playbooks['pb1'].pk
        pk2 = two_playbooks['pb2'].pk
        page.goto(f"{live_server_url}/browser/{pk1}/")
        page.wait_for_load_state('domcontentloaded')

        page.evaluate(f"_pushPlaybookUrl({pk2}, {{types: [], phases: []}})")
        expect(page).to_have_url(f"{live_server_url}/browser/{pk2}/")

        page.go_back()
        expect(page).to_have_url(f"{live_server_url}/browser/{pk1}/")

    # FOB-CONTENT-BROWSER-03b
    def test_active_filters_reflected_in_url_query_params(self, page: Page, live_server_url, playbook_with_phases):
        """Active type/phase filters appear as query params in the URL."""
        _login(page, live_server_url, playbook_with_phases['username'], playbook_with_phases['password'])
        pk = playbook_with_phases['pb'].pk
        phase_id = playbook_with_phases['phase1'].pk
        page.goto(f"{live_server_url}/browser/{pk}/")
        page.wait_for_load_state('domcontentloaded')

        page.evaluate(
            f"_pushPlaybookUrl({pk}, {{types: ['workflow', 'activity'], phases: [{phase_id}]}})"
        )

        url = page.url
        assert 'types=workflow%2Cactivity' in url or 'types=workflow,activity' in url

    # FOB-CONTENT-BROWSER-03b
    def test_default_state_has_no_query_params(self, page: Page, live_server_url, playbook_with_phases):
        """When all types visible and no phase filter: URL is clean (no query string)."""
        _login(page, live_server_url, playbook_with_phases['username'], playbook_with_phases['password'])
        pk = playbook_with_phases['pb'].pk
        page.goto(f"{live_server_url}/browser/{pk}/")
        page.wait_for_load_state('domcontentloaded')

        page.evaluate(
            "const allTypes = ['workflow','activity','skill','agent','artifact','rule','phase'];"
            f"_pushPlaybookUrl({pk}, {{types: allTypes, phases: []}})"
        )

        expect(page).to_have_url(f"{live_server_url}/browser/{pk}/")

    # FOB-CONTENT-BROWSER-03b
    def test_shared_url_restores_filter_state(self, page: Page, live_server_url, playbook_with_phases):
        """Navigating directly to /browser/<pk>/?types=workflow,activity restores filters."""
        _login(page, live_server_url, playbook_with_phases['username'], playbook_with_phases['password'])
        pk = playbook_with_phases['pb'].pk
        page.goto(f"{live_server_url}/browser/{pk}/?types=workflow,activity")
        page.wait_for_load_state('domcontentloaded')

        filters = page.evaluate("_parseUrlParams()")
        assert filters['types'] == ['workflow', 'activity']

    # FOB-CONTENT-BROWSER-03f
    def test_empty_types_param_treated_as_all_types_shown(self, page: Page, live_server_url, seeded_playbook):
        """?types= (empty) → all entity types visible, URL rewritten to canonical."""
        _login(page, live_server_url, seeded_playbook['username'], seeded_playbook['password'])
        pk = seeded_playbook['pb'].pk
        page.goto(f"{live_server_url}/browser/{pk}/?types=")
        page.wait_for_load_state('domcontentloaded')

        # types='' → all types active → canonical URL has no types param
        expect(page).to_have_url(f"{live_server_url}/browser/{pk}/")

    # FOB-CONTENT-BROWSER-03f
    def test_unknown_phase_ids_dropped_on_load(self, page: Page, live_server_url, seeded_playbook):
        """Phase IDs not present in the playbook are dropped and URL rewritten."""
        _login(page, live_server_url, seeded_playbook['username'], seeded_playbook['password'])
        pk = seeded_playbook['pb'].pk
        valid_phase_id = seeded_playbook['phase'].pk
        invalid_id = valid_phase_id + 99999
        page.goto(f"{live_server_url}/browser/{pk}/?phases={invalid_id}")
        page.wait_for_load_state('domcontentloaded')

        # After init, invalid phase IDs are dropped → canonical URL has no phases param
        expect(page).to_have_url(f"{live_server_url}/browser/{pk}/")

    # FOB-CONTENT-BROWSER-03f
    def test_invalid_params_do_not_hide_content(self, page: Page, live_server_url, seeded_playbook):
        """Invalid params result in graph rendering normally (nothing hidden, no error)."""
        _login(page, live_server_url, seeded_playbook['username'], seeded_playbook['password'])
        pk = seeded_playbook['pb'].pk
        page.goto(f"{live_server_url}/browser/{pk}/?types=bogus&phases=abc,999")
        page.wait_for_load_state('domcontentloaded')

        # Browser chrome rendered — left panel always visible
        expect(page.get_by_test_id('browser-left-panel')).to_be_visible()
        # Error state NOT shown — invalid params are normalised, not errored
        expect(page.get_by_test_id('browser-error-state')).to_be_hidden()
