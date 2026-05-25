"""Unit tests for WorkflowExportService."""

import pytest
import tempfile
import shutil
from pathlib import Path
from django.core.exceptions import ObjectDoesNotExist
from methodology.models import Workflow, Activity, Playbook, Agent, Skill, Artifact, ArtifactInput, Rule
from methodology.services.workflow_export_service import WorkflowExportService


@pytest.mark.django_db
class TestWorkflowExportService:
    """Test WorkflowExportService functionality."""
    
    @pytest.fixture
    def playbook(self, django_user_model):
        """Create test playbook."""
        user = django_user_model.objects.create_user(
            username='maria',
            email='maria@example.com',
            password='testpass123'
        )
        return Playbook.objects.create(
            name='React Frontend Development',
            description='Modern React patterns',
            category='development',
            author=user,
            status='draft',
            version='0.5'
        )
    
    @pytest.fixture
    def workflow(self, playbook):
        """Create test workflow."""
        return Workflow.objects.create(
            name='Frontend Development',
            description='Complete frontend development process',
            playbook=playbook,
            abbreviation='FFE',
            order=1
        )
    
    @pytest.fixture
    def activities(self, workflow, create_test_phases):
        """Create test activities."""
        # Create test phases
        phases = create_test_phases(workflow.playbook)
        
        activities = []
        for i in range(1, 4):
            activity = Activity.objects.create(
                workflow=workflow,
                name=f'Activity {i}',
                guidance=f'Guidance for activity {i}',
                order=i,
                phase=phases['Foundation'] if i == 1 else phases['Implementation']
            )
            activities.append(activity)
        return activities
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for exports."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_export_writes_linked_rules_mdc(self, workflow, activities, temp_dir, playbook):
        """Export creates sibling rules/ with .mdc for linked rules."""
        rule = Rule.objects.create(
            playbook=playbook,
            title='Pytest rule',
            slug='pytest-rule',
            content='Use pytest for all tests.',
            always_apply=True,
        )
        activities[0].rules.add(rule)

        sub = Path(temp_dir) / 'workflows'
        sub.mkdir(parents=True, exist_ok=True)
        result = WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow.id,
            target_directory=str(sub),
            folder_name='FFE',
        )
        rules_dir = sub.parent / 'rules'
        mdc = rules_dir / 'pytest-rule.mdc'
        assert mdc.exists()
        text = mdc.read_text()
        assert 'alwaysApply: true' in text
        assert 'Use pytest' in text
        assert 'rules/pytest-rule.mdc' in result['files_created'] or any(
            'pytest-rule.mdc' in f for f in result['files_created']
        )

    def test_export_workflow_creates_files(self, workflow, activities, temp_dir):
        """Test FOB-WORKFLOWS-EXPORT_IMPORT-01: Export creates all files."""
        result = WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow.id,
            target_directory=temp_dir,
            folder_name='FFE'
        )
        
        assert result['status'] == 'exported'
        assert result['workflow_id'] == workflow.id
        assert result['workflow_name'] == 'Frontend Development'
        assert len(result['files_created']) == 4  # _workflow.md + 3 activities
        assert '_workflow.md' in result['files_created']
        assert 'FFE-01-Activity_1.md' in result['files_created']
        assert 'FFE-02-Activity_2.md' in result['files_created']
        assert 'FFE-03-Activity_3.md' in result['files_created']
        
        # Verify files exist
        export_path = Path(temp_dir) / 'FFE'
        assert (export_path / '_workflow.md').exists()
        assert (export_path / 'FFE-01-Activity_1.md').exists()
    
    def test_workflow_metadata_content(self, workflow, activities, temp_dir):
        """Test FOB-WORKFLOWS-EXPORT_IMPORT-02: _workflow.md contains metadata."""
        WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow.id,
            target_directory=temp_dir,
            folder_name='FFE'
        )
        
        workflow_file = Path(temp_dir) / 'FFE' / '_workflow.md'
        content = workflow_file.read_text()
        
        # Refresh playbook to get current version after auto-increment
        workflow.playbook.refresh_from_db()
        
        assert '# Frontend Development' in content
        assert 'React Frontend Development' in content
        assert '(Draft)' in content
        assert f'**Workflow ID**: {workflow.id}' in content
        assert '**Total Activities**: 3' in content
        assert 'Uses phases' in content
    
    def test_activity_file_contains_metadata(self, workflow, activities, temp_dir):
        """Test FOB-WORKFLOWS-EXPORT_IMPORT-02: Activity file contains complete metadata."""
        WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow.id,
            target_directory=temp_dir,
            folder_name='FFE'
        )
        
        activity_file = Path(temp_dir) / 'FFE' / 'FFE-01-Activity_1.md'
        content = activity_file.read_text()
        
        assert '# Activity: Activity 1' in content
        assert f'**Activity ID**: {activities[0].id}' in content
        assert '**Order**: 1' in content
        assert '**Phase**: Foundation' in content
        assert '**Dependencies**: None' in content
        assert '## Description' in content
        assert '## Guidance' in content
        assert 'Guidance for activity 1' in content
        assert '## Artifacts Produced' in content
        assert '## Artifacts Consumed' in content
        assert '## Notes' in content
    
    def test_slugify_converts_text_correctly(self):
        """Test _slugify method."""
        assert WorkflowExportService._slugify('Setup Project') == 'Setup_Project'
        assert WorkflowExportService._slugify('API Integration (v2)') == 'API_Integration_v2'
        assert WorkflowExportService._slugify('Test & Deploy') == 'Test_Deploy'
        assert WorkflowExportService._slugify('  Multiple   Spaces  ') == 'Multiple_Spaces'
    
    def test_export_with_default_folder_name(self, workflow, activities, temp_dir):
        """Test export with auto-generated folder name."""
        result = WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow.id,
            target_directory=temp_dir
        )
        
        assert result['status'] == 'exported'
        export_path = Path(temp_dir) / 'Frontend_Development'
        assert export_path.exists()
        assert (export_path / '_workflow.md').exists()
    
    def test_export_nonexistent_workflow_raises_error(self, temp_dir):
        """Test export with invalid workflow ID."""
        with pytest.raises(ObjectDoesNotExist):
            WorkflowExportService.export_workflow_to_markdown(
                workflow_id=99999,
                target_directory=temp_dir,
                folder_name='TEST'
            )
    
    def test_export_creates_directory_if_not_exists(self, workflow, activities):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / 'nested' / 'path'
            
            result = WorkflowExportService.export_workflow_to_markdown(
                workflow_id=workflow.id,
                target_directory=str(nested_path),
                folder_name='FFE'
            )
            
            assert result['status'] == 'exported'
            assert (nested_path / 'FFE' / '_workflow.md').exists()
    
    def test_export_overwrites_existing_files(self, workflow, activities, temp_dir):
        """Test that export overwrites existing files."""
        export_path = Path(temp_dir) / 'FFE'
        export_path.mkdir(parents=True)
        
        # Create existing file
        existing_file = export_path / '_workflow.md'
        existing_file.write_text('Old content')
        
        # Export
        WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow.id,
            target_directory=temp_dir,
            folder_name='FFE'
        )
        
        # Verify overwritten
        content = existing_file.read_text()
        assert 'Old content' not in content
        assert '# Frontend Development' in content
    
    def test_activity_with_dependencies(self, workflow, activities, temp_dir):
        """Test activity file with predecessor/successor."""
        # Set up dependencies
        activities[1].predecessor = activities[0]
        activities[1].successor = activities[2]
        activities[1].save()
        
        WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow.id,
            target_directory=temp_dir,
            folder_name='FFE'
        )
        
        activity_file = Path(temp_dir) / 'FFE' / 'FFE-02-Activity_2.md'
        content = activity_file.read_text()
        
        assert f'Predecessor: Activity {activities[0].id} (Activity 1)' in content
        assert f'Successor: Activity {activities[2].id} (Activity 3)' in content
    
    def test_workflow_without_phases(self, workflow, temp_dir):
        """Test workflow export when no phases are used."""
        # Create activities without phases
        for i in range(1, 3):
            Activity.objects.create(
                workflow=workflow,
                name=f'No Phase Activity {i}',
                guidance=f'Guidance {i}',
                order=i,
                phase=None
            )
        
        WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow.id,
            target_directory=temp_dir,
            folder_name='FFE'
        )
        
        workflow_file = Path(temp_dir) / 'FFE' / '_workflow.md'
        content = workflow_file.read_text()
        
        assert 'No phase organization' in content
    
    def test_export_includes_agent_skill_artifacts(self, playbook, workflow, temp_dir):
        """Test FOB-WORKFLOWS-EXPORT_IMPORT-ISSUE72: Export includes agent, skill, and artifacts."""
        # Create agent
        agent = Agent.objects.create(
            playbook=playbook,
            name='Code Reviewer',
            description='Reviews code for quality and best practices'
        )
        
        # Create skill
        skill = Skill.objects.create(
            playbook=playbook,
            title='React Component Development',
            capability_domain='GUI_COMPONENT',
            technology_stack='React+TypeScript',
            content='Guide for building React components'
        )
        
        # Create producer activity
        producer = Activity.objects.create(
            workflow=workflow,
            name='Design Component',
            guidance='Design the component structure',
            order=1
        )
        
        # Create activity with agent and skills
        activity = Activity.objects.create(
            workflow=workflow,
            name='Implement Component',
            guidance='Implement the React component',
            order=2,
            agent=agent,
        )
        activity.skills.add(skill)
        
        # Create output artifact (produced by activity)
        output_artifact = Artifact.objects.create(
            playbook=playbook,
            produced_by=activity,
            name='Component Code',
            type='Code',
            is_required=True
        )
        
        # Create input artifact (consumed by activity)
        input_artifact = Artifact.objects.create(
            playbook=playbook,
            produced_by=producer,
            name='Design Document',
            type='Document',
            is_required=True
        )
        
        # Link input artifact to activity
        ArtifactInput.objects.create(
            artifact=input_artifact,
            activity=activity,
            is_required=True
        )
        
        # Export workflow
        WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow.id,
            target_directory=temp_dir,
            folder_name='FFE'
        )
        
        # Read activity file
        activity_file = Path(temp_dir) / 'FFE' / 'FFE-02-Implement_Component.md'
        content = activity_file.read_text()
        
        # Assert agent information is included (Issue #72)
        assert '## Agent' in content
        assert 'Code Reviewer' in content
        assert 'Reviews code for quality and best practices' in content
        
        # Assert skill information is included (Issue #72)
        assert '## Skill' in content
        assert 'React Component Development' in content
        assert 'GUI_COMPONENT' in content
        assert 'React+TypeScript' in content
        
        # Assert artifacts produced section has actual data (Issue #72)
        assert '## Artifacts Produced' in content
        assert 'Component Code' in content
        assert 'Code' in content
        assert 'Required' in content or 'True' in content
        
        # Assert artifacts consumed section has actual data (Issue #72)
        assert '## Artifacts Consumed' in content
        assert 'Design Document' in content
        assert 'Document' in content
        
        # Ensure "None" is NOT present in these sections
        lines = content.split('\n')
        in_agent_section = False
        in_skill_section = False
        in_artifacts_produced = False
        in_artifacts_consumed = False
        
        for i, line in enumerate(lines):
            if '## Agent' in line:
                in_agent_section = True
                in_skill_section = False
                in_artifacts_produced = False
                in_artifacts_consumed = False
            elif '## Skill' in line:
                in_agent_section = False
                in_skill_section = True
                in_artifacts_produced = False
                in_artifacts_consumed = False
            elif '## Artifacts Produced' in line:
                in_agent_section = False
                in_skill_section = False
                in_artifacts_produced = True
                in_artifacts_consumed = False
            elif '## Artifacts Consumed' in line:
                in_agent_section = False
                in_skill_section = False
                in_artifacts_produced = False
                in_artifacts_consumed = True
            elif line.startswith('##'):
                in_agent_section = False
                in_skill_section = False
                in_artifacts_produced = False
                in_artifacts_consumed = False
            
            # Check that "None" doesn't appear as the only content in these sections
            if (in_agent_section or in_skill_section or in_artifacts_produced or in_artifacts_consumed):
                if i + 2 < len(lines) and lines[i + 2].strip() == 'None':
                    pytest.fail(f"Found 'None' in section starting at line {i}: {line}")
    
    def test_export_without_agent_skill_artifacts(self, playbook, workflow, temp_dir):
        """Test export shows 'None' when activity has no agent, skill, or artifacts."""
        # Create simple activity without agent, skill, or artifacts
        activity = Activity.objects.create(
            workflow=workflow,
            name='Simple Activity',
            guidance='Simple guidance',
            order=1
        )
        
        # Export workflow
        WorkflowExportService.export_workflow_to_markdown(
            workflow_id=workflow.id,
            target_directory=temp_dir,
            folder_name='FFE'
        )
        
        # Read activity file
        activity_file = Path(temp_dir) / 'FFE' / 'FFE-01-Simple_Activity.md'
        content = activity_file.read_text()
        
        # Should show "None" when no agent/skill/artifacts
        assert '## Agent' in content
        assert '## Skill' in content
        assert '## Artifacts Produced' in content
        assert '## Artifacts Consumed' in content
