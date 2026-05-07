"""Integration tests for playbook-scoped activity list (/playbooks/<pk>/activities/)."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from methodology.models import Activity, Playbook, Workflow

User = get_user_model()


@pytest.fixture
def activity_list_playbook_setup(db):
    owner = User.objects.create_user(username='act_list_owner', password='secret')
    other = User.objects.create_user(username='act_list_other', password='secret')
    pb_a = Playbook.objects.create(
        name='Playbook A',
        description='d',
        category='development',
        status='active',
        source='owned',
        author=owner,
    )
    pb_b = Playbook.objects.create(
        name='Playbook B',
        description='d',
        category='development',
        status='active',
        source='owned',
        author=owner,
    )
    wf_a = Workflow.objects.create(playbook=pb_a, name='WF A', description='d', order=1)
    wf_b = Workflow.objects.create(playbook=pb_b, name='WF B', description='d', order=1)
    Activity.objects.create(workflow=wf_a, name='A1', guidance='g', order=1)
    Activity.objects.create(workflow=wf_a, name='A2', guidance='g', order=2)
    Activity.objects.create(workflow=wf_b, name='B1', guidance='g', order=1)
    return {'owner': owner, 'other': other, 'pb_a': pb_a}


@pytest.mark.django_db
class TestActivityListForPlaybook:
    def test_url_resolves_with_reverse(self, activity_list_playbook_setup):
        pb = activity_list_playbook_setup['pb_a']
        assert reverse(
            'activity_list_for_playbook',
            kwargs={'playbook_pk': pb.pk},
        ) == f'/playbooks/{pb.pk}/activities/'

    def test_owner_sees_only_their_playbook_activities(self, activity_list_playbook_setup):
        client = Client()
        client.force_login(activity_list_playbook_setup['owner'])
        pb_a = activity_list_playbook_setup['pb_a']
        url = reverse('activity_list_for_playbook', kwargs={'playbook_pk': pb_a.pk})
        response = client.get(url)
        assert response.status_code == 200
        body = response.content.decode()
        assert 'A1' in body and 'A2' in body
        assert 'B1' not in body

    def test_non_owner_blocked(self, activity_list_playbook_setup):
        client = Client()
        client.force_login(activity_list_playbook_setup['other'])
        pb_a = activity_list_playbook_setup['pb_a']
        response = client.get(
            reverse('activity_list_for_playbook', kwargs={'playbook_pk': pb_a.pk})
        )
        assert response.status_code == 404

    def test_unauthenticated_redirects_to_login(self, activity_list_playbook_setup):
        pb_a = activity_list_playbook_setup['pb_a']
        response = Client().get(
            reverse('activity_list_for_playbook', kwargs={'playbook_pk': pb_a.pk})
        )
        assert response.status_code == 302
        assert response['Location'].startswith('/auth/user/login/')

    def test_template_used(self, activity_list_playbook_setup):
        client = Client()
        client.force_login(activity_list_playbook_setup['owner'])
        pb_a = activity_list_playbook_setup['pb_a']
        response = client.get(
            reverse('activity_list_for_playbook', kwargs={'playbook_pk': pb_a.pk})
        )
        names = [t.name for t in (response.templates or []) if getattr(t, 'name', None)]
        assert 'activities/playbook_list.html' in names

    def test_zero_activities_renders_empty_state(self, db):
        user = User.objects.create_user(username='empty_acts', password='x')
        pb = Playbook.objects.create(
            name='Empty PB',
            description='d',
            category='development',
            status='active',
            source='owned',
            author=user,
        )
        Workflow.objects.create(playbook=pb, name='Lonely', description='d', order=1)
        client = Client()
        client.force_login(user)
        response = client.get(
            reverse('activity_list_for_playbook', kwargs={'playbook_pk': pb.pk})
        )
        assert response.status_code == 200
        assert b'No activities yet' in response.content
        assert b'data-testid="empty-state"' in response.content
