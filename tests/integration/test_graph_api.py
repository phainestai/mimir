"""
Integration tests for Content Browser Graph API endpoint.

Covers: FOB-CONTENT-BROWSER-13, 13b (activity phase metadata), 13c (session expiry redirect),
        13d (404 on deleted playbook), 13e (per-activity resource scoping),
        13f (display_code on activity nodes), 13g (sequence edges).
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from methodology.models import (
    Playbook, Workflow, Activity, Phase, Skill, Agent, Artifact, Rule,
    ArtifactInput, Team, TeamMembership, TeamPlaybook,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='graph_user',
        email='graph@test.com',
        password='testpass123',
    )


@pytest.fixture
def auth_client(user):
    token = Token.objects.create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


@pytest.fixture
def released_playbook(user, db):
    """A released playbook with one workflow, two activities, one phase."""
    pb = Playbook.objects.create(
        name='FeatureFactory',
        description='Test playbook',
        category='development',
        status='released',
        version='1.0',
        source='owned',
        author=user,
    )
    phase = Phase.objects.create(playbook=pb, name='Construction', order=1)
    wf = Workflow.objects.create(
        name='BPE', description='Build Phase Execution',
        playbook=pb, order=1,
    )
    act1 = Activity.objects.create(
        name='Plan', workflow=wf, order=1, phase=phase,
    )
    act2 = Activity.objects.create(
        name='Implement', workflow=wf, order=2, predecessor=act1,
    )
    return pb


@pytest.fixture
def playbook_with_resources(user, db):
    """Playbook with skill, agent, artifact, rule linked to an activity."""
    pb = Playbook.objects.create(
        name='ResourcePlaybook',
        description='Has resources',
        category='development',
        status='released',
        version='1.0',
        source='owned',
        author=user,
    )
    wf = Workflow.objects.create(name='Workflow A', playbook=pb, order=1)
    skill = Skill.objects.create(playbook=pb, title='Build Skill')
    agent = Agent.objects.create(playbook=pb, name='Build Agent')
    rule = Rule.objects.create(playbook=pb, title='Build Rule')
    act = Activity.objects.create(name='Build', workflow=wf, order=1, agent=agent)
    act.skills.add(skill)
    act.rules.add(rule)
    artifact = Artifact.objects.create(
        name='Build Output',
        playbook=pb,
        produced_by=act,
    )
    return pb


@pytest.fixture
def empty_playbook(user, db):
    """Released playbook with no workflows."""
    return Playbook.objects.create(
        name='EmptyPlaybook',
        description='No workflows',
        category='development',
        status='released',
        version='1.0',
        source='owned',
        author=user,
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username='other_user',
        email='other@test.com',
        password='testpass123',
    )


@pytest.fixture
def private_playbook(other_user, db):
    """Private playbook owned by other_user — inaccessible to graph_user."""
    return Playbook.objects.create(
        name='PrivatePlaybook',
        description='Private',
        category='development',
        status='released',
        version='1.0',
        source='owned',
        author=other_user,
        visibility='private',
    )


@pytest.fixture
def team_playbook_access(db, other_user):
    """Private team playbook: other_user owns; graph_user is team member."""
    member = User.objects.get(username='graph_user')
    playbook = Playbook.objects.create(
        name='Team Shared Playbook',
        description='Shared via team',
        category='development',
        status='released',
        version='1.0',
        source='owned',
        author=other_user,
        visibility='private',
    )
    Workflow.objects.create(playbook=playbook, name='Team WF', order=1)
    team = Team.objects.create(
        name='Graph API Team',
        visibility=Team.VISIBILITY_HIDDEN,
        admin=other_user,
    )
    TeamMembership.objects.create(team=team, user=other_user, role='admin')
    TeamMembership.objects.create(team=team, user=member, role='member')
    TeamPlaybook.objects.create(team=team, playbook=playbook)
    return {'playbook': playbook, 'member': member, 'owner': other_user}


# ---------------------------------------------------------------------------
# FOB-CONTENT-BROWSER-13: Authentication and access
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGraphAPIAccess:

    def test_graph_requires_authentication(self, api_client, released_playbook):
        """Unauthenticated request returns 401."""
        url = f'/api/playbooks/{released_playbook.pk}/graph/'
        response = api_client.get(url)
        assert response.status_code == 401

    def test_graph_returns_404_for_inaccessible_playbook(self, auth_client, private_playbook):
        """Private playbook owned by another user returns 404."""
        url = f'/api/playbooks/{private_playbook.pk}/graph/'
        response = auth_client.get(url)
        assert response.status_code == 404

    def test_graph_returns_404_for_nonexistent_playbook(self, auth_client):
        """Non-existent playbook PK returns 404."""
        response = auth_client.get('/api/playbooks/99999/graph/')
        assert response.status_code == 404

    def test_team_member_can_access_team_playbook_graph(self, auth_client, team_playbook_access):
        """Team member can load graph API for a private team playbook (Act-16 A1)."""
        playbook = team_playbook_access['playbook']
        url = f'/api/playbooks/{playbook.pk}/graph/'
        response = auth_client.get(url)
        assert response.status_code == 200, response.content
        data = response.json()
        assert data['playbook_name'] == 'Team Shared Playbook'
        assert len(data['nodes']) >= 1

    def test_team_playbook_appears_in_playbook_list_api(self, auth_client, team_playbook_access):
        """GET /api/playbooks/ includes team-shared playbooks for members (Act-16 A1)."""
        playbook = team_playbook_access['playbook']
        response = auth_client.get('/api/playbooks/')
        assert response.status_code == 200
        ids = [item['id'] for item in response.data['results']]
        assert playbook.pk in ids

    def test_graph_owner_can_access_own_playbook(self, auth_client, released_playbook):
        """Owner can access their own playbook graph (FOB-CONTENT-BROWSER-13)."""
        url = f'/api/playbooks/{released_playbook.pk}/graph/'
        response = auth_client.get(url)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# FOB-CONTENT-BROWSER-13: Response structure
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGraphAPIResponseShape:

    def test_graph_response_has_required_top_level_keys(self, auth_client, released_playbook):
        """Response must have nodes, edges, phases keys."""
        url = f'/api/playbooks/{released_playbook.pk}/graph/'
        response = auth_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert 'nodes' in data
        assert 'edges' in data
        assert 'phases' in data

    def test_empty_playbook_returns_empty_nodes_and_edges(self, auth_client, empty_playbook):
        """Playbook with no workflows returns empty nodes and edges."""
        url = f'/api/playbooks/{empty_playbook.pk}/graph/'
        response = auth_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data['nodes'] == []
        assert data['edges'] == []
        assert data['phases'] == []

    def test_workflow_node_has_required_fields(self, auth_client, released_playbook):
        """Workflow node must have: id, type, label, entity_pk, detail_url, embed_url, meta."""
        url = f'/api/playbooks/{released_playbook.pk}/graph/'
        data = auth_client.get(url).json()
        wf_nodes = [n for n in data['nodes'] if n['type'] == 'workflow']
        assert len(wf_nodes) >= 1
        node = wf_nodes[0]
        for field in ('id', 'type', 'label', 'entity_pk', 'detail_url', 'embed_url', 'meta'):
            assert field in node, f'Missing field: {field}'

    def test_workflow_node_id_is_namespaced(self, auth_client, released_playbook):
        """Workflow node IDs must use 'workflow:<pk>' namespace."""
        data = auth_client.get(f'/api/playbooks/{released_playbook.pk}/graph/').json()
        wf_nodes = [n for n in data['nodes'] if n['type'] == 'workflow']
        for node in wf_nodes:
            assert node['id'].startswith('workflow:'), f"Bad id: {node['id']}"

    def test_activity_node_id_is_namespaced(self, auth_client, released_playbook):
        """Activity node IDs must use 'activity:<pk>' namespace."""
        data = auth_client.get(f'/api/playbooks/{released_playbook.pk}/graph/').json()
        act_nodes = [n for n in data['nodes'] if n['type'] == 'activity']
        assert len(act_nodes) >= 1
        for node in act_nodes:
            assert node['id'].startswith('activity:'), f"Bad id: {node['id']}"

    def test_edge_has_required_fields(self, auth_client, released_playbook):
        """Every edge must have source, target, relationship."""
        data = auth_client.get(f'/api/playbooks/{released_playbook.pk}/graph/').json()
        assert len(data['edges']) >= 1
        for edge in data['edges']:
            for field in ('source', 'target', 'relationship'):
                assert field in edge, f'Edge missing field: {field}'

    def test_detail_url_and_embed_url_are_present(self, auth_client, released_playbook):
        """detail_url and embed_url must be non-empty strings."""
        data = auth_client.get(f'/api/playbooks/{released_playbook.pk}/graph/').json()
        for node in data['nodes']:
            assert isinstance(node['detail_url'], str), f"detail_url not str on {node['id']}"
            assert len(node['detail_url']) > 0, f"detail_url empty on {node['id']}"
            assert isinstance(node['embed_url'], str), f"embed_url not str on {node['id']}"
            # embed_url should append ?embed=1 to detail_url
            assert node['embed_url'].endswith('?embed=1'), f"embed_url missing ?embed=1 on {node['id']}"

    def test_phase_array_contains_required_fields(self, auth_client, released_playbook):
        """Each phase must have id, name, colour."""
        data = auth_client.get(f'/api/playbooks/{released_playbook.pk}/graph/').json()
        assert len(data['phases']) >= 1
        phase = data['phases'][0]
        for field in ('id', 'name', 'colour'):
            assert field in phase, f'Phase missing field: {field}'
        assert phase['colour'].startswith('#'), "Phase colour must be hex string"


# ---------------------------------------------------------------------------
# FOB-CONTENT-BROWSER-13b: Activity phase metadata# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGraphAPIPhaseMetadata:

    def test_activity_with_phase_carries_phase_meta(self, auth_client, released_playbook):
        """Activity assigned to a phase includes phase_id, phase_name, phase_colour in meta."""
        data = auth_client.get(f'/api/playbooks/{released_playbook.pk}/graph/').json()
        act_nodes = [n for n in data['nodes'] if n['type'] == 'activity']
        phased = [n for n in act_nodes if n['meta'].get('phase_id')]
        assert len(phased) >= 1, 'Expected at least one activity with phase'
        node = phased[0]
        assert 'phase_id' in node['meta']
        assert 'phase_name' in node['meta']
        assert 'phase_colour' in node['meta']
        assert node['meta']['phase_colour'].startswith('#')

    def test_activity_without_phase_has_empty_meta(self, auth_client, released_playbook):
        """Activity without a phase has empty meta (no phase_id)."""
        data = auth_client.get(f'/api/playbooks/{released_playbook.pk}/graph/').json()
        act_nodes = [n for n in data['nodes'] if n['type'] == 'activity']
        unphased = [n for n in act_nodes if not n['meta'].get('phase_id')]
        assert len(unphased) >= 1, 'Expected at least one activity without phase'


# ---------------------------------------------------------------------------
# FOB-CONTENT-BROWSER-13c: Contains edges
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGraphAPIContainsEdges:

    def test_contains_edge_from_workflow_to_activity(self, auth_client, released_playbook):
        """Each activity must have a 'contains' edge from its parent workflow."""
        data = auth_client.get(f'/api/playbooks/{released_playbook.pk}/graph/').json()
        contains_edges = [e for e in data['edges'] if e['relationship'] == 'contains']
        assert len(contains_edges) >= 2  # two activities in released_playbook

    def test_predecessor_edge_emitted(self, auth_client, released_playbook):
        """Predecessor relationship emits a 'predecessor' typed edge."""
        data = auth_client.get(f'/api/playbooks/{released_playbook.pk}/graph/').json()
        pred_edges = [e for e in data['edges'] if e['relationship'] == 'predecessor']
        assert len(pred_edges) >= 1

    def test_edges_reference_only_emitted_nodes(self, auth_client, released_playbook):
        """Every edge source and target must exist in the nodes list."""
        data = auth_client.get(f'/api/playbooks/{released_playbook.pk}/graph/').json()
        node_ids = {n['id'] for n in data['nodes']}
        for edge in data['edges']:
            assert edge['source'] in node_ids, f"Dangling source: {edge['source']}"
            assert edge['target'] in node_ids, f"Dangling target: {edge['target']}"


# ---------------------------------------------------------------------------
# FOB-CONTENT-BROWSER-13d: Resource edges (skills, agents, artifacts, rules)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGraphAPIResourceEdges:

    def test_skill_node_and_uses_skill_edge_present(self, auth_client, playbook_with_resources):
        """Skill appears as a per-activity node; 'uses_skill' edge connects activity to skill."""
        data = auth_client.get(f'/api/playbooks/{playbook_with_resources.pk}/graph/').json()
        skill_nodes = [n for n in data['nodes'] if n['type'] == 'skill']
        assert len(skill_nodes) == 1
        assert skill_nodes[0]['id'].startswith('skill:')
        assert ':activity:' in skill_nodes[0]['id'], 'Skill node must be scoped per-activity'
        uses_edges = [e for e in data['edges'] if e['relationship'] == 'uses_skill']
        assert len(uses_edges) == 1

    def test_agent_node_and_assigned_agent_edge_present(self, auth_client, playbook_with_resources):
        """Agent appears as a per-activity node; 'assigned_agent' edge connects activity to agent."""
        data = auth_client.get(f'/api/playbooks/{playbook_with_resources.pk}/graph/').json()
        agent_nodes = [n for n in data['nodes'] if n['type'] == 'agent']
        assert len(agent_nodes) == 1
        assert agent_nodes[0]['id'].startswith('agent:')
        assert ':activity:' in agent_nodes[0]['id'], 'Agent node must be scoped per-activity'
        agent_edges = [e for e in data['edges'] if e['relationship'] == 'assigned_agent']
        assert len(agent_edges) == 1

    def test_rule_node_and_governed_by_rule_edge_present(self, auth_client, playbook_with_resources):
        """Rule appears as a per-activity node; 'governed_by_rule' edge connects activity to rule."""
        data = auth_client.get(f'/api/playbooks/{playbook_with_resources.pk}/graph/').json()
        rule_nodes = [n for n in data['nodes'] if n['type'] == 'rule']
        assert len(rule_nodes) == 1
        assert rule_nodes[0]['id'].startswith('rule:')
        assert ':activity:' in rule_nodes[0]['id'], 'Rule node must be scoped per-activity'
        rule_edges = [e for e in data['edges'] if e['relationship'] == 'governed_by_rule']
        assert len(rule_edges) == 1

    def test_artifact_node_and_produces_edge_present(self, auth_client, playbook_with_resources):
        """Artifact appears as a per-activity node; 'produces' edge connects activity to artifact."""
        data = auth_client.get(f'/api/playbooks/{playbook_with_resources.pk}/graph/').json()
        artifact_nodes = [n for n in data['nodes'] if n['type'] == 'artifact']
        assert len(artifact_nodes) == 1
        assert artifact_nodes[0]['id'].startswith('artifact:')
        assert ':activity:' in artifact_nodes[0]['id'], 'Artifact node must be scoped per-activity'
        produces_edges = [e for e in data['edges'] if e['relationship'] == 'produces']
        assert len(produces_edges) == 1

    def test_no_duplicate_node_ids(self, auth_client, playbook_with_resources):
        """All node IDs must be globally unique (per-activity scoping guarantees this)."""
        data = auth_client.get(f'/api/playbooks/{playbook_with_resources.pk}/graph/').json()
        ids = [n['id'] for n in data['nodes']]
        assert len(ids) == len(set(ids)), 'Duplicate node IDs found'

    def test_same_resource_linked_to_two_activities_creates_two_nodes(self, user, auth_client, db):
        """Same skill on two activities → two distinct per-activity nodes, two edges (FOB-13e)."""
        pb = Playbook.objects.create(
            name='SharedResource', description='', category='development',
            status='released', version='1.0', source='owned', author=user,
        )
        wf = Workflow.objects.create(name='WF', playbook=pb, order=1)
        skill = Skill.objects.create(playbook=pb, title='Shared Skill')
        act1 = Activity.objects.create(name='Step 1', workflow=wf, order=1)
        act2 = Activity.objects.create(name='Step 2', workflow=wf, order=2)
        act1.skills.add(skill)
        act2.skills.add(skill)

        data = auth_client.get(f'/api/playbooks/{pb.pk}/graph/').json()
        skill_nodes = [n for n in data['nodes'] if n['type'] == 'skill']
        assert len(skill_nodes) == 2, 'Shared skill must produce two per-activity nodes'
        ids = {n['id'] for n in skill_nodes}
        assert f'skill:{skill.pk}:activity:{act1.pk}' in ids
        assert f'skill:{skill.pk}:activity:{act2.pk}' in ids
        # entity_pk is the same on both — they represent the same underlying entity
        assert all(n['entity_pk'] == skill.pk for n in skill_nodes)
        uses_edges = [e for e in data['edges'] if e['relationship'] == 'uses_skill']
        assert len(uses_edges) == 2

    def test_cross_playbook_resources_not_emitted(self, user, auth_client, db):
        """Skills from another playbook must NOT appear as nodes in this playbook's graph."""
        other_pb = Playbook.objects.create(
            name='OtherPB', description='', category='development',
            status='released', version='1.0', source='owned', author=user,
        )
        orphan_skill = Skill.objects.create(playbook=other_pb, title='Orphan Skill')

        pb = Playbook.objects.create(
            name='TargetPB', description='', category='development',
            status='released', version='1.0', source='owned', author=user,
        )
        wf = Workflow.objects.create(name='WF', playbook=pb, order=1)
        act = Activity.objects.create(name='Act', workflow=wf, order=1)
        act.skills.add(orphan_skill)  # cross-playbook M2M link

        data = auth_client.get(f'/api/playbooks/{pb.pk}/graph/').json()
        skill_nodes = [n for n in data['nodes'] if n['type'] == 'skill']
        assert not any(n['entity_pk'] == orphan_skill.pk for n in skill_nodes), \
            'Cross-playbook skill must not appear in graph'


# ---------------------------------------------------------------------------
# FOB-CONTENT-BROWSER-13f/13g: display_code and sequence edges
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGraphAPIDisplayCodeAndSequence:

    @pytest.fixture
    def ordered_playbook(self, user, db):
        """Playbook with a workflow (abbreviation BPE) and three ordered activities."""
        pb = Playbook.objects.create(
            name='OrderedPB', description='', category='development',
            status='released', version='1.0', source='owned', author=user,
        )
        wf = Workflow.objects.create(name='Build Phase', abbreviation='BPE', playbook=pb, order=1)
        act1 = Activity.objects.create(name='Plan', workflow=wf, order=1)
        act2 = Activity.objects.create(name='Implement', workflow=wf, order=2)
        act3 = Activity.objects.create(name='Test', workflow=wf, order=3)
        return pb, wf, act1, act2, act3

    def test_activity_node_includes_display_code(self, auth_client, ordered_playbook):
        """Activity nodes include meta.display_code with format '<abbr>-<order>' (FOB-13f)."""
        pb, wf, act1, act2, act3 = ordered_playbook
        data = auth_client.get(f'/api/playbooks/{pb.pk}/graph/').json()
        act_nodes = {n['entity_pk']: n for n in data['nodes'] if n['type'] == 'activity'}
        assert act_nodes[act1.pk]['meta']['display_code'] == 'BPE-1'
        assert act_nodes[act2.pk]['meta']['display_code'] == 'BPE-2'
        assert act_nodes[act3.pk]['meta']['display_code'] == 'BPE-3'

    def test_activity_display_code_empty_when_no_abbreviation(self, user, auth_client, db):
        """Activity node display_code is empty string when workflow has no abbreviation.

        NOTE: Workflow.save() auto-generates abbreviation from the name, so we bypass
        it by using update() to force an empty abbreviation after creation.
        """
        pb = Playbook.objects.create(
            name='NoAbbrPB', description='', category='development',
            status='released', version='1.0', source='owned', author=user,
        )
        from methodology.models import Workflow as WorkflowModel
        wf = Workflow.objects.create(name='No Abbr Workflow', playbook=pb, order=1)
        # Force empty abbreviation via queryset update (bypasses save() auto-gen)
        WorkflowModel.objects.filter(pk=wf.pk).update(abbreviation='')
        act = Activity.objects.create(name='Solo', workflow=wf, order=1)
        data = auth_client.get(f'/api/playbooks/{pb.pk}/graph/').json()
        act_nodes = [n for n in data['nodes'] if n['type'] == 'activity']
        assert len(act_nodes) == 1
        assert act_nodes[0]['meta']['display_code'] == ''

    def test_sequence_edges_emitted_in_order(self, auth_client, ordered_playbook):
        """Consecutive activities produce sequence edges: 1→2→3 (FOB-13g)."""
        pb, wf, act1, act2, act3 = ordered_playbook
        data = auth_client.get(f'/api/playbooks/{pb.pk}/graph/').json()
        seq_edges = [e for e in data['edges'] if e['relationship'] == 'sequence']
        assert len(seq_edges) == 2
        sources = {e['source'] for e in seq_edges}
        targets = {e['target'] for e in seq_edges}
        assert f'activity:{act1.pk}' in sources
        assert f'activity:{act2.pk}' in sources
        assert f'activity:{act2.pk}' in targets
        assert f'activity:{act3.pk}' in targets

    def test_single_activity_workflow_has_no_sequence_edge(self, user, auth_client, db):
        """A workflow with one activity emits no sequence edge."""
        pb = Playbook.objects.create(
            name='SingleActPB', description='', category='development',
            status='released', version='1.0', source='owned', author=user,
        )
        wf = Workflow.objects.create(name='Solo WF', playbook=pb, order=1)
        Activity.objects.create(name='Solo', workflow=wf, order=1)
        data = auth_client.get(f'/api/playbooks/{pb.pk}/graph/').json()
        seq_edges = [e for e in data['edges'] if e['relationship'] == 'sequence']
        assert len(seq_edges) == 0

    def test_sequence_edges_not_cross_workflow(self, user, auth_client, db):
        """Sequence edges are NOT emitted across different workflows."""
        pb = Playbook.objects.create(
            name='TwoWFPB', description='', category='development',
            status='released', version='1.0', source='owned', author=user,
        )
        wf1 = Workflow.objects.create(name='WF One', playbook=pb, order=1)
        wf2 = Workflow.objects.create(name='WF Two', playbook=pb, order=2)
        act1 = Activity.objects.create(name='WF1 Act', workflow=wf1, order=1)
        act2 = Activity.objects.create(name='WF2 Act', workflow=wf2, order=1)
        data = auth_client.get(f'/api/playbooks/{pb.pk}/graph/').json()
        seq_edges = [e for e in data['edges'] if e['relationship'] == 'sequence']
        # Single-activity workflows → no sequence edges
        assert len(seq_edges) == 0
        # Confirm no edge crosses the two workflows
        cross = [e for e in seq_edges
                 if e['source'] == f'activity:{act1.pk}' and e['target'] == f'activity:{act2.pk}']
        assert len(cross) == 0
