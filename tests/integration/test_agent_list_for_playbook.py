"""Integration tests for playbook-scoped agent list (/playbooks/<pk>/agents/)."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from methodology.models import Agent, Playbook

User = get_user_model()


@pytest.fixture
def agent_list_playbook_setup(db):
    owner = User.objects.create_user(username='ag_list_owner', password='secret')
    other = User.objects.create_user(username='ag_list_other', password='secret')
    pb_a = Playbook.objects.create(
        name='Agents PB A',
        description='d',
        category='development',
        status='active',
        source='owned',
        author=owner,
    )
    pb_b = Playbook.objects.create(
        name='Agents PB B',
        description='d',
        category='development',
        status='active',
        source='owned',
        author=owner,
    )
    Agent.objects.create(playbook=pb_a, name='Alpha', description='d1')
    Agent.objects.create(playbook=pb_a, name='Beta', description='d2')
    Agent.objects.create(playbook=pb_b, name='Gamma', description='d3')
    return {'owner': owner, 'other': other, 'pb_a': pb_a}


@pytest.mark.django_db
class TestAgentListForPlaybook:
    def test_url_resolves_with_reverse(self, agent_list_playbook_setup):
        pb = agent_list_playbook_setup['pb_a']
        assert reverse(
            'agent_list_for_playbook',
            kwargs={'playbook_pk': pb.pk},
        ) == f'/playbooks/{pb.pk}/agents/'

    def test_owner_sees_only_their_playbook_agents(self, agent_list_playbook_setup):
        client = Client()
        client.force_login(agent_list_playbook_setup['owner'])
        pb_a = agent_list_playbook_setup['pb_a']
        response = client.get(
            reverse('agent_list_for_playbook', kwargs={'playbook_pk': pb_a.pk})
        )
        assert response.status_code == 200
        body = response.content.decode()
        assert 'Alpha' in body and 'Beta' in body
        assert 'Gamma' not in body

    def test_non_owner_blocked(self, agent_list_playbook_setup):
        client = Client()
        client.force_login(agent_list_playbook_setup['other'])
        pb_a = agent_list_playbook_setup['pb_a']
        response = client.get(
            reverse('agent_list_for_playbook', kwargs={'playbook_pk': pb_a.pk})
        )
        assert response.status_code == 404

    def test_unauthenticated_redirects_to_login(self, agent_list_playbook_setup):
        pb_a = agent_list_playbook_setup['pb_a']
        response = Client().get(
            reverse('agent_list_for_playbook', kwargs={'playbook_pk': pb_a.pk})
        )
        assert response.status_code == 302
        assert response['Location'].startswith('/auth/user/login/')

    def test_template_used(self, agent_list_playbook_setup):
        client = Client()
        client.force_login(agent_list_playbook_setup['owner'])
        pb_a = agent_list_playbook_setup['pb_a']
        response = client.get(
            reverse('agent_list_for_playbook', kwargs={'playbook_pk': pb_a.pk})
        )
        names = [t.name for t in (response.templates or []) if getattr(t, 'name', None)]
        assert 'agents/playbook_list.html' in names

    def test_zero_agents_renders_empty_state(self, db):
        user = User.objects.create_user(username='empty_ag', password='x')
        pb = Playbook.objects.create(
            name='No Agents PB',
            description='d',
            category='development',
            status='active',
            source='owned',
            author=user,
        )
        client = Client()
        client.force_login(user)
        response = client.get(
            reverse('agent_list_for_playbook', kwargs={'playbook_pk': pb.pk})
        )
        assert response.status_code == 200
        assert b'No agents yet' in response.content
        assert b'data-testid="empty-state"' in response.content
