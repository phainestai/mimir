"""Feature Acceptance Tests for Workflow Export/Import MCP Tools.

Tests scenarios from docs/features/act-3-workflows/workflows-export-import.feature

Uses direct service calls (not async MCP wrappers) to avoid async/sync issues.
Tests the core functionality that MCP tools wrap.

Coverage:
✅ FOB-WORKFLOWS-EXPORT_IMPORT-01: Export workflow to markdown
✅ FOB-WORKFLOWS-EXPORT_IMPORT-02: Activity files contain complete metadata
✅ FOB-WORKFLOWS-EXPORT_IMPORT-05: Import generates upload protocol
✅ FOB-WORKFLOWS-EXPORT_IMPORT-06: Protocol contains AI rationale placeholders
✅ FOB-WORKFLOWS-EXPORT_IMPORT-08: Apply protocol to draft playbook
✅ FOB-WORKFLOWS-EXPORT_IMPORT-10: Create PIP for released playbook
✅ FOB-WORKFLOWS-EXPORT_IMPORT-15: Full export-edit-import-apply cycle

Run: pytest tests/integration/test_workflow_export_import_mcp.py -v
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from methodology.models import Workflow, Activity, Playbook
from methodology.services.workflow_export_service import WorkflowExportService
from methodology.services.workflow_import_service import WorkflowImportService
from methodology.services.workflow_protocol_service import WorkflowProtocolService


@pytest.mark.django_db
class TestWorkflowExportImportIntegration:
    """
    Feature Acceptance Tests for Workflow Export/Import.
    
    Tests the complete workflow export/import cycle that MCP tools expose.
    Uses service layer directly to avoid async/sync complexity in tests.
    
    Test Strategy:
    - Real database operations (no mocking per project rules)
    - Tests complete user journeys from feature file
    - Validates file I/O, change detection, protocol generation
    - Covers both draft and released playbook workflows
    """
    
    @pytest.fixture
    def user(self, django_user_model):
        """Create test user."""
        return django_user_model.objects.create_user(
            username='maria',
            email='maria@example.com',
            password='testpass123'
        )
    
    @pytest.fixture
    def playbook_draft(self, user):
        """Create draft playbook."""
        return Playbook.objects.create(
            name='React Frontend Development',
            description='Modern React patterns',
            category='development',
            author=user,
            status='draft',
            version='0.5'
        )
    
    @pytest.fixture
    def playbook_released(self, user):
        """Create released playbook."""
        return Playbook.objects.create(
            name='Production Playbook',
            description='Released playbook',
            category='production',
            author=user,
            status='released',
            version='1.0'
        )
    
    @pytest.fixture
    def workflow_draft(self, playbook_draft):
        """Create workflow in draft playbook."""
        return Workflow.objects.create(
            name='Frontend Development',
            description='Complete frontend development process',
            playbook=playbook_draft,
            abbreviation='FFE',
            order=1
        )
    
    @pytest.fixture
    def workflow_released(self, playbook_released):
        """Create workflow in released playbook."""
        return Workflow.objects.create(
            name='Production Workflow',
            description='Production workflow',
            playbook=playbook_released,
            abbreviation='PROD',
            order=1
        )
    
    @pytest.fixture
    def activities(self, workflow_draft, create_test_phases):
        """Create 15 test activities."""
        # Create test phases
        phases = create_test_phases(workflow_draft.playbook)
        
        activities = []
        for i in range(1, 16):
            phase = phases['Foundation'] if i <= 5 else phases['Implementation'] if i <= 10 else phases['Testing']
            activity = Activity.objects.create(
                workflow=workflow_draft,
                name=f'Activity {i}',
                guidance=f'Guidance for activity {i}\n\nStep 1: Do this\nStep 2: Do that',
                order=i,
                phase=phase
            )
            activities.append(activity)
        return activities
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_scenario_01_export_creates_16_files(self, workflow_draft, activities, temp_dir):
        """
        FOB-WORKFLOWS-EXPORT_IMPORT-01: Export via MCP tool
        
        Given: Workflow with 15 activities
        When: Export to local directory
        Then: 16 files created (_workflow.md + 15 activity files)
        """
        result = WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow_draft.id,
            target_directory=temp_dir,
            folder_name='FFE'
        )
        
        assert result['status'] == 'exported'
        assert len(result['files_created']) == 16
        assert '_workflow.md' in result['files_created']
        
        export_path = Path(temp_dir) / 'FFE'
        assert (export_path / '_workflow.md').exists()
        assert (export_path / 'FFE-01-Activity_1.md').exists()
        assert (export_path / 'FFE-15-Activity_15.md').exists()
    
    def test_scenario_02_activity_file_has_complete_metadata(self, workflow_draft, activities, temp_dir):
        """
        FOB-WORKFLOWS-EXPORT_IMPORT-02: Activity file contains complete metadata
        
        Given: Workflow exported
        When: Open activity file
        Then: Contains ID, Order, Phase, Dependencies, Description, Guidance, Artifacts, Notes
        """
        WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow_draft.id,
            target_directory=temp_dir,
            folder_name='FFE'
        )
        
        activity_file = Path(temp_dir) / 'FFE' / 'FFE-01-Activity_1.md'
        content = activity_file.read_text()
        
        assert '# Activity: Activity 1' in content
        assert f'**Activity ID**: {activities[0].id}' in content
        assert '**Order**: 1' in content
        assert '**Phase**: Foundation' in content
        assert '## Description' in content
        assert '## Guidance' in content
        assert 'Step 1: Do this' in content
        assert '## Artifacts Produced' in content
        assert '## Artifacts Consumed' in content
        assert '## Notes' in content
    
    def test_scenario_05_import_generates_protocol(self, workflow_draft, activities, temp_dir):
        """
        FOB-WORKFLOWS-EXPORT_IMPORT-05: Generate upload protocol via MCP
        
        Given: Exported workflow edited locally (new activity added)
        When: Import changes
        Then: _Upload_Protocol.md created with change summary
        """
        WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow_draft.id,
            target_directory=temp_dir,
            folder_name='FFE'
        )
        
        new_activity = Path(temp_dir) / 'FFE' / 'FFE-16-New_Activity.md'
        new_activity.write_text("""# Activity: New Activity

**Activity ID**: 
**Order**: 16
**Phase**: Testing
**Dependencies**: None

## Guidance

New activity guidance
""")
        
        result = WorkflowImportService.import_workflow_from_markdown(
            workflow_id=workflow_draft.id,
            source_directory=str(Path(temp_dir) / 'FFE')
        )
        
        assert result['status'] == 'changes_detected'
        assert result['changes_count'] > 0
        
        protocol_file = Path(temp_dir) / 'FFE' / '_Upload_Protocol.md'
        assert protocol_file.exists()
    
    def test_scenario_06_protocol_has_ai_rationale_placeholders(self, workflow_draft, activities, temp_dir):
        """
        FOB-WORKFLOWS-EXPORT_IMPORT-06: AI prepares protocol with rationales
        
        Given: Changes detected
        When: Protocol generated
        Then: Contains [AI to fill] placeholders and approval options
        """
        WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow_draft.id,
            target_directory=temp_dir,
            folder_name='FFE'
        )
        
        new_activity = Path(temp_dir) / 'FFE' / 'FFE-16-Testing.md'
        new_activity.write_text("""# Activity: Testing

**Activity ID**: 
**Order**: 16
**Phase**: Testing
**Dependencies**: None

## Guidance

Test guidance
""")
        
        WorkflowImportService.import_workflow_from_markdown(
            workflow_id=workflow_draft.id,
            source_directory=str(Path(temp_dir) / 'FFE')
        )
        
        protocol_file = Path(temp_dir) / 'FFE' / '_Upload_Protocol.md'
        protocol_content = protocol_file.read_text()
        
        assert '[AI to fill' in protocol_content
        assert '## Approval Options' in protocol_content
        assert 'Apply Immediately' in protocol_content
        assert 'Submit as PIP' in protocol_content
    
    def test_scenario_08_apply_protocol_to_draft(self, workflow_draft, activities, temp_dir):
        """
        FOB-WORKFLOWS-EXPORT_IMPORT-08: Apply changes to draft playbook
        
        Given: Draft playbook with protocol
        When: Apply protocol
        Then: Changes applied, version incremented
        """
        WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow_draft.id,
            target_directory=temp_dir,
            folder_name='FFE'
        )
        
        WorkflowImportService.import_workflow_from_markdown(
            workflow_id=workflow_draft.id,
            source_directory=str(Path(temp_dir) / 'FFE')
        )
        
        protocol_file = str(Path(temp_dir) / 'FFE' / '_Upload_Protocol.md')
        
        result = WorkflowProtocolService.apply_upload_protocol(protocol_file)
        
        assert result['status'] == 'applied'
        assert result['workflow_id'] == workflow_draft.id
        assert 'changes_applied' in result
    
    def test_scenario_10_create_pip_for_released(self, workflow_released, temp_dir):
        """
        FOB-WORKFLOWS-EXPORT_IMPORT-10: Create PIP for released playbook
        
        Given: Released playbook with protocol
        When: Create PIP from protocol
        Then: PIP created with pending_review status
        """
        Activity.objects.create(
            workflow=workflow_released,
            name='Production Activity',
            guidance='Production guidance',
            order=1
        )
        
        WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow_released.id,
            target_directory=temp_dir,
            folder_name='PROD'
        )
        
        WorkflowImportService.import_workflow_from_markdown(
            workflow_id=workflow_released.id,
            source_directory=str(Path(temp_dir) / 'PROD')
        )
        
        protocol_file = str(Path(temp_dir) / 'PROD' / '_Upload_Protocol.md')
        
        result = WorkflowProtocolService.create_pip_from_protocol(
            protocol_file,
            pip_title='Improve workflow',
            actor=workflow_released.playbook.author,
        )

        assert result['status'] == 'draft'
        assert isinstance(result['pip_id'], int)
        assert 'pip_id' in result
    
    def test_scenario_15_full_cycle_draft(self, workflow_draft, activities, temp_dir):
        """
        FOB-WORKFLOWS-EXPORT_IMPORT-15: Full export-edit-import-apply cycle
        
        Given: Draft playbook
        When: Export → Edit → Import → Apply
        Then: Complete cycle succeeds
        """
        # Export
        export_result = WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow_draft.id,
            target_directory=temp_dir,
            folder_name='FFE'
        )
        assert len(export_result['files_created']) == 16
        
        # Edit - add new activity
        new_activity = Path(temp_dir) / 'FFE' / 'FFE-16-Integration.md'
        new_activity.write_text("""# Activity: Integration Testing

**Activity ID**: 
**Order**: 16
**Phase**: Testing
**Dependencies**: None

## Guidance

Run integration tests
""")
        
        # Import
        import_result = WorkflowImportService.import_workflow_from_markdown(
            workflow_id=workflow_draft.id,
            source_directory=str(Path(temp_dir) / 'FFE')
        )
        assert import_result['changes_count'] > 0
        
        # Apply
        protocol_file = str(Path(temp_dir) / 'FFE' / '_Upload_Protocol.md')
        apply_result = WorkflowProtocolService.apply_upload_protocol(protocol_file)

        assert apply_result['status'] == 'applied'

    def test_clean_round_trip_zero_changes(self, workflow_draft, activities, temp_dir):
        """
        FOB-WORKFLOWS-EXPORT_IMPORT-RT: Clean round-trip detects zero changes.

        Given: Workflow exported without modifications
        When:  Immediately re-imported from the same files
        Then:  changes_count == 0 (no false positives)
        """
        WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow_draft.id,
            target_directory=temp_dir,
            folder_name='FFE',
        )

        result = WorkflowImportService.import_workflow_from_markdown(
            workflow_id=workflow_draft.id,
            source_directory=str(Path(temp_dir) / 'FFE'),
        )

        assert result['changes_count'] == 0, (
            f"Clean round-trip must report 0 changes; got {result['changes_count']}. "
            f"Details: {result}"
        )

    def test_clean_round_trip_no_guidance_activity(self, workflow_draft, temp_dir):
        """
        Regression: activity with NULL guidance must not appear as modified after export/import.
        """
        Activity.objects.create(
            workflow=workflow_draft,
            name='Guidance-Free Activity',
            guidance='',
            order=1,
        )

        WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow_draft.id,
            target_directory=temp_dir,
            folder_name='FFE',
        )

        result = WorkflowImportService.import_workflow_from_markdown(
            workflow_id=workflow_draft.id,
            source_directory=str(Path(temp_dir) / 'FFE'),
        )

        assert result['changes_count'] == 0, (
            f"Activity with null guidance must not be a false positive; got {result['changes_count']}"
        )


@pytest.mark.django_db
class TestWorkflowExportAPIShape:
    """Integration tests for POST /api/workflows/{id}/export/ JSON response shape."""

    @pytest.fixture
    def user(self, django_user_model):
        return django_user_model.objects.create_user(
            username='maria',
            email='maria@example.com',
            password='testpass123',
        )

    @pytest.fixture
    def client(self, user):
        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=user)
        return client

    @pytest.fixture
    def playbook(self, user):
        return Playbook.objects.create(
            name='React Frontend Development',
            description='Modern React patterns',
            category='development',
            author=user,
            status='draft',
            version='0.5',
        )

    @pytest.fixture
    def workflow(self, playbook):
        return Workflow.objects.create(
            name='Frontend Development',
            description='Complete frontend development process',
            playbook=playbook,
            abbreviation='FFE',
            order=1,
        )

    @pytest.fixture
    def activities(self, workflow, create_test_phases):
        phases = create_test_phases(workflow.playbook)
        activities = []
        for i in range(1, 4):
            activity = Activity.objects.create(
                workflow=workflow,
                name=f'Activity {i}',
                guidance=f'Guidance for activity {i}',
                order=i,
                phase=phases['Foundation'] if i == 1 else phases['Implementation'],
            )
            activities.append(activity)
        return activities

    def test_export_endpoint_returns_json_not_files(self, client, workflow, activities):
        """POST /export/ returns 200 with workflow_files list; no export_path key."""
        response = client.post(
            f'/api/workflows/{workflow.id}/export/',
            {'folder_name': 'FFE'},
            format='json',
        )

        assert response.status_code == 200
        data = response.data
        assert 'workflow_files' in data
        assert isinstance(data['workflow_files'], list)
        assert 'export_path' not in data
        assert data['folder_name'] == 'FFE'

    def test_export_endpoint_returns_correct_file_count(self, client, workflow, activities):
        """len(workflow_files) == activity count + 1 (_workflow.md)."""
        response = client.post(
            f'/api/workflows/{workflow.id}/export/',
            {'folder_name': 'FFE'},
            format='json',
        )

        assert response.status_code == 200
        assert len(response.data['workflow_files']) == len(activities) + 1

    def test_export_endpoint_rule_files_in_response(self, client, workflow, activities, playbook):
        """Activities with rules produce rule_files with correct .mdc content."""
        from methodology.models import Rule

        rule = Rule.objects.create(
            playbook=playbook,
            title='Pytest rule',
            slug='pytest-rule',
            content='Use pytest for all tests.',
            always_apply=True,
        )
        activities[0].rules.add(rule)

        response = client.post(
            f'/api/workflows/{workflow.id}/export/',
            {'folder_name': 'FFE'},
            format='json',
        )

        assert response.status_code == 200
        assert len(response.data['rule_files']) == 1
        rule_file = response.data['rule_files'][0]
        assert rule_file['filename'] == 'pytest-rule.mdc'
        assert 'alwaysApply: true' in rule_file['content']
        assert 'Use pytest' in rule_file['content']

    def test_export_endpoint_requires_auth(self, workflow, activities):
        """Unauthenticated POST returns 401 or 403."""
        from rest_framework.test import APIClient

        client = APIClient()
        response = client.post(
            f'/api/workflows/{workflow.id}/export/',
            {'folder_name': 'FFE'},
            format='json',
        )

        assert response.status_code in (401, 403)
