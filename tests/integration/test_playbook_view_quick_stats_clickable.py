"""
Integration tests: Quick Stats on playbook detail link to playbook-scoped lists.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from methodology.models import Playbook

User = get_user_model()

STAT_LINK_ROWS = (
    ('workflows', 'workflow_list', 'playbook_pk'),
    ('phases', 'phase_list', 'playbook_pk'),
    ('activities', 'activity_list_for_playbook', 'playbook_pk'),
    ('artifacts', 'artifact_list', 'playbook_id'),
    ('agents', 'agent_list_for_playbook', 'playbook_pk'),
    ('skills', 'skill_list_playbook', 'playbook_pk'),
    ('rules', 'rule_list_playbook', 'playbook_pk'),
)


@pytest.fixture
def playbook_quick_links(db):
    user = User.objects.create_user(username='qs_links_user', password='secret')
    playbook = Playbook.objects.create(
        name='QS Links Playbook',
        description='d',
        category='development',
        status='active',
        source='owned',
        author=user,
    )
    return {'user': user, 'playbook': playbook}


@pytest.mark.django_db
@pytest.mark.parametrize('slug, url_name, kw', STAT_LINK_ROWS)
def test_quick_stat_tile_href_and_destination_ok(slug, url_name, kw, playbook_quick_links):
    user = playbook_quick_links['user']
    playbook = playbook_quick_links['playbook']
    client = Client()
    client.force_login(user)

    detail = client.get(reverse('playbook_detail', kwargs={'pk': playbook.pk}))
    assert detail.status_code == 200
    html = detail.content.decode()

    kwargs = {kw: playbook.pk}
    expected_href = reverse(url_name, kwargs=kwargs)
    anchor_testid = f'stat-{slug}-link'
    assert f'data-testid="{anchor_testid}"' in html
    assert f'href="{expected_href}"' in html

    dest = client.get(expected_href)
    assert dest.status_code == 200
