"""
Integration tests for embed mode (?embed=1) on 7 entity detail views.

Covers: FOB-CONTENT-BROWSER-08b
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from methodology.models import (
    Activity, Agent, Artifact, ArtifactInput, Phase, Playbook, Rule, Skill,
    Workflow,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='embed_user',
        email='embed@test.com',
        password='testpass',
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username='embed_other',
        email='other@test.com',
        password='testpass',
    )


@pytest.fixture
def client_auth(user):
    c = Client()
    c.force_login(user)
    return c


@pytest.fixture
def playbook(user, db):
    return Playbook.objects.create(
        name='EmbedPlaybook',
        description='For embed tests',
        category='development',
        status='draft',
        version='0.1',
        source='owned',
        author=user,
    )


@pytest.fixture
def workflow(playbook):
    return Workflow.objects.create(
        playbook=playbook,
        name='EmbedWorkflow',
        description='Workflow for embed',
        order=1,
    )


@pytest.fixture
def activity(workflow, playbook):
    return Activity.objects.create(
        workflow=workflow,
        name='EmbedActivity',
        guidance='**Bold** guidance',
        order=1,
    )


@pytest.fixture
def skill(playbook):
    return Skill.objects.create(
        playbook=playbook,
        title='EmbedSkill',
        content='Skill **content**',
        capability_domain='TESTING',
    )


@pytest.fixture
def agent(playbook):
    return Agent.objects.create(
        playbook=playbook,
        name='EmbedAgent',
        description='Agent *description*',
    )


@pytest.fixture
def rule(playbook):
    return Rule.objects.create(
        playbook=playbook,
        title='EmbedRule',
        slug='embed-rule',
        content='Rule **content**',
        always_apply=True,
    )


@pytest.fixture
def artifact(playbook, activity):
    return Artifact.objects.create(
        playbook=playbook,
        name='EmbedArtifact',
        type='Document',
        description='Artifact desc',
        produced_by=activity,
        is_required=True,
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _embed_url(url):
    sep = '&' if '?' in url else '?'
    return f'{url}{sep}embed=1'


# ---------------------------------------------------------------------------
# Embed mode returns fragment (no outer chrome)
# ---------------------------------------------------------------------------

class TestEmbedReturnsFragment:
    """Each entity returns a plain HTML fragment with no outer chrome."""

    def _assert_fragment(self, response, entity_name):
        assert response.status_code == 200
        content = response.content.decode()
        assert '<html' not in content, "embed should not contain <html>"
        assert 'main-navbar' not in content, "embed should not contain navbar"
        assert entity_name in content, f"embed should contain entity name '{entity_name}'"

    def test_playbook_embed(self, client_auth, playbook):
        url = _embed_url(reverse('playbook_detail', kwargs={'pk': playbook.pk}))
        self._assert_fragment(client_auth.get(url), 'EmbedPlaybook')

    def test_workflow_embed(self, client_auth, playbook, workflow):
        url = _embed_url(
            reverse('workflow_detail', kwargs={'playbook_pk': playbook.pk, 'pk': workflow.pk})
        )
        self._assert_fragment(client_auth.get(url), 'EmbedWorkflow')

    def test_activity_embed(self, client_auth, playbook, workflow, activity):
        url = _embed_url(
            reverse('activity_detail', kwargs={
                'playbook_pk': playbook.pk,
                'workflow_pk': workflow.pk,
                'activity_pk': activity.pk,
            })
        )
        self._assert_fragment(client_auth.get(url), 'EmbedActivity')

    def test_skill_embed(self, client_auth, playbook, skill):
        url = _embed_url(
            reverse('skill_detail', kwargs={'playbook_pk': playbook.pk, 'skill_pk': skill.pk})
        )
        self._assert_fragment(client_auth.get(url), 'EmbedSkill')

    def test_agent_embed(self, client_auth, agent):
        url = _embed_url(reverse('agent_detail', kwargs={'pk': agent.pk}))
        self._assert_fragment(client_auth.get(url), 'EmbedAgent')

    def test_rule_embed(self, client_auth, playbook, rule):
        url = _embed_url(
            reverse('rule_detail', kwargs={'playbook_pk': playbook.pk, 'rule_pk': rule.pk})
        )
        self._assert_fragment(client_auth.get(url), 'EmbedRule')

    def test_artifact_embed(self, client_auth, artifact):
        url = _embed_url(reverse('artifact_detail', kwargs={'pk': artifact.pk}))
        self._assert_fragment(client_auth.get(url), 'EmbedArtifact')

    def test_activity_embed_renders_markdown_guidance(self, client_auth, playbook, workflow, activity):
        """Markdown in guidance must be rendered to HTML, not shown raw."""
        url = _embed_url(
            reverse('activity_detail', kwargs={
                'playbook_pk': playbook.pk,
                'workflow_pk': workflow.pk,
                'activity_pk': activity.pk,
            })
        )
        content = client_auth.get(url).content.decode()
        assert '<strong>' in content, "markdown should be rendered to HTML"
        assert '**Bold**' not in content, "raw markdown should not appear"


# ---------------------------------------------------------------------------
# Full-page view unchanged (regression)
# ---------------------------------------------------------------------------

class TestFullPageUnchanged:
    """Without ?embed=1 the normal full-page response is returned."""

    def _assert_full_page(self, response):
        assert response.status_code == 200
        content = response.content.decode()
        assert 'main-navbar' in content, "full page should contain navbar"
        assert '<html' in content, "full page should contain <html>"

    def test_playbook_full_page(self, client_auth, playbook):
        url = reverse('playbook_detail', kwargs={'pk': playbook.pk})
        self._assert_full_page(client_auth.get(url))

    def test_workflow_full_page(self, client_auth, playbook, workflow):
        url = reverse('workflow_detail', kwargs={'playbook_pk': playbook.pk, 'pk': workflow.pk})
        self._assert_full_page(client_auth.get(url))

    def test_activity_full_page(self, client_auth, playbook, workflow, activity):
        url = reverse('activity_detail', kwargs={
            'playbook_pk': playbook.pk,
            'workflow_pk': workflow.pk,
            'activity_pk': activity.pk,
        })
        self._assert_full_page(client_auth.get(url))

    def test_skill_full_page(self, client_auth, playbook, skill):
        url = reverse('skill_detail', kwargs={'playbook_pk': playbook.pk, 'skill_pk': skill.pk})
        self._assert_full_page(client_auth.get(url))

    def test_agent_full_page(self, client_auth, agent):
        url = reverse('agent_detail', kwargs={'pk': agent.pk})
        self._assert_full_page(client_auth.get(url))

    def test_rule_full_page(self, client_auth, playbook, rule):
        url = reverse('rule_detail', kwargs={'playbook_pk': playbook.pk, 'rule_pk': rule.pk})
        self._assert_full_page(client_auth.get(url))

    def test_artifact_full_page(self, client_auth, artifact):
        url = reverse('artifact_detail', kwargs={'pk': artifact.pk})
        self._assert_full_page(client_auth.get(url))


# ---------------------------------------------------------------------------
# Anonymous user → 302 redirect to login
# ---------------------------------------------------------------------------

class TestEmbedAnonymousRedirects:
    """Anonymous requests on ?embed=1 URLs redirect to login (login_required)."""

    def test_playbook_embed_anonymous(self, client, playbook):
        url = _embed_url(reverse('playbook_detail', kwargs={'pk': playbook.pk}))
        assert client.get(url).status_code == 302

    def test_workflow_embed_anonymous(self, client, playbook, workflow):
        url = _embed_url(
            reverse('workflow_detail', kwargs={'playbook_pk': playbook.pk, 'pk': workflow.pk})
        )
        assert client.get(url).status_code == 302

    def test_activity_embed_anonymous(self, client, playbook, workflow, activity):
        url = _embed_url(
            reverse('activity_detail', kwargs={
                'playbook_pk': playbook.pk,
                'workflow_pk': workflow.pk,
                'activity_pk': activity.pk,
            })
        )
        assert client.get(url).status_code == 302

    def test_skill_embed_anonymous(self, client, playbook, skill):
        url = _embed_url(
            reverse('skill_detail', kwargs={'playbook_pk': playbook.pk, 'skill_pk': skill.pk})
        )
        assert client.get(url).status_code == 302

    def test_agent_embed_anonymous(self, client, agent):
        url = _embed_url(reverse('agent_detail', kwargs={'pk': agent.pk}))
        assert client.get(url).status_code == 302

    def test_rule_embed_anonymous(self, client, playbook, rule):
        url = _embed_url(
            reverse('rule_detail', kwargs={'playbook_pk': playbook.pk, 'rule_pk': rule.pk})
        )
        assert client.get(url).status_code == 302

    def test_artifact_embed_anonymous(self, client, artifact):
        url = _embed_url(reverse('artifact_detail', kwargs={'pk': artifact.pk}))
        assert client.get(url).status_code == 302
