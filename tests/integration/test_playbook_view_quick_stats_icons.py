"""
Integration tests for Playbook detail page — Quick Stats icon consistency.

Each Quick Stats tile must display the canonical entity icon from the
navbar (single source of truth in ``templates/base.html``).
"""

import re

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from methodology.models import Playbook

User = get_user_model()


@pytest.fixture
def playbook_for_stats(db):
    """Create a minimal playbook so the detail page renders Quick Stats."""
    user = User.objects.create_user(username='stats_user', password='test123')
    playbook = Playbook.objects.create(
        name='StatsPlaybook',
        description='Quick stats fixture',
        category='development',
        status='active',
        source='owned',
        author=user,
    )
    return {'user': user, 'playbook': playbook}


def _quick_stats_skill_tile(html: str) -> str:
    """Extract the Skills tile markup from the playbook detail page HTML."""
    match = re.search(
        r'<div[^>]*data-testid="stat-skills"[^>]*>.*?</div>',
        html, re.DOTALL,
    )
    assert match is not None, "Quick Stats skills tile not found"
    return match.group(0)


@pytest.mark.django_db
class TestQuickStatsSkillsIcon:
    """The Skills tile must use the canonical skill icon, not the PIP one."""

    def test_skills_tile_uses_hand_holding_magic_icon(self, playbook_for_stats):
        """Skills tile renders ``fa-hand-holding-magic`` per navbar source of truth."""
        client = Client()
        client.force_login(playbook_for_stats['user'])

        response = client.get(
            reverse('playbook_detail', kwargs={'pk': playbook_for_stats['playbook'].pk})
        )
        assert response.status_code == 200

        tile_html = _quick_stats_skill_tile(response.content.decode('utf-8'))
        assert 'fa-hand-holding-magic' in tile_html, (
            f"Skills tile missing fa-hand-holding-magic icon: {tile_html!r}"
        )

    def test_skills_tile_does_not_use_lightbulb_icon(self, playbook_for_stats):
        """Skills tile must not reuse the PIP icon (``fa-lightbulb``)."""
        client = Client()
        client.force_login(playbook_for_stats['user'])

        response = client.get(
            reverse('playbook_detail', kwargs={'pk': playbook_for_stats['playbook'].pk})
        )

        tile_html = _quick_stats_skill_tile(response.content.decode('utf-8'))
        assert 'fa-lightbulb' not in tile_html, (
            f"Skills tile wrongly uses fa-lightbulb: {tile_html!r}"
        )
