"""Pytest configuration and fixtures for Mimir tests."""

import pytest
from django.core.management import call_command
from methodology.models import Phase


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Configure database for E2E tests and load fixtures.
    
    Loads test data from tests/fixtures/e2e_seed.json once at session start.
    """
    with django_db_blocker.unblock():
        # Load E2E test fixtures
        call_command('loaddata', 'tests/fixtures/e2e_seed.json')


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Enable database access for all tests by default.
    """
    pass


@pytest.fixture(autouse=True)
def block_real_email_sends(request, settings):
    """Force locmem mail backend for every test except @pytest.mark.live_ses.

    Prevents accidental SES sends when pytest runs with prod-like env vars.
    """
    if request.node.get_closest_marker("live_ses"):
        return
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


@pytest.fixture
def create_test_phases(db):
    """
    Helper fixture to create standard test phases for a playbook.
    
    Usage:
        phases = create_test_phases(playbook)
        # Returns dict: {'Planning': <Phase>, 'Execution': <Phase>, ...}
    """
    def _create_phases(playbook):
        """Create standard test phases for the given playbook."""
        phase_data = [
            ('Planning', 'Planning phase', 1),
            ('Execution', 'Execution phase', 2),
            ('Foundation', 'Foundation phase', 3),
            ('Implementation', 'Implementation phase', 4),
            ('Testing', 'Testing phase', 5),
        ]
        
        phases = {}
        for name, description, order in phase_data:
            phase, _ = Phase.objects.get_or_create(
                playbook=playbook,
                name=name,
                defaults={'description': description, 'order': order}
            )
            phases[name] = phase
        
        return phases
    
    return _create_phases
