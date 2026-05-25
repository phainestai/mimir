"""Workflow Export Service - Export workflows to markdown files."""

import logging
import re
from pathlib import Path
from typing import Optional
from django.core.exceptions import ObjectDoesNotExist
from methodology.models import Workflow
from methodology.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)


class WorkflowExportService:
    """Service for exporting workflows to markdown files."""
    
    @staticmethod
    def export_workflow_to_markdown(
        workflow_id: int,
        target_directory: str,
        folder_name: Optional[str] = None,
        user=None,
    ) -> dict:
        """
        Export workflow and activities as markdown files.
        
        :param workflow_id: Workflow ID. Example: 42
        :param target_directory: Target directory path. Example: ".windsurf/workflows"
        :param folder_name: Folder name. Example: "FFE" (defaults to workflow slug)
        :param user: When set, only export if user may view the parent playbook
        :return: Export result dict with file paths and counts
        :raises ObjectDoesNotExist: If workflow does not exist
        :raises PermissionError: If user may not view workflow playbook
        :raises PermissionError: If directory not writable
        """
        logger.info(f"Exporting workflow {workflow_id} to {target_directory}")
        
        try:
            if user is not None:
                workflow = WorkflowService.get_workflow_for_user(
                    workflow_id, user, write=False, prefetch_activities=False
                )
            else:
                workflow = Workflow.objects.select_related('playbook').get(pk=workflow_id)
        except ObjectDoesNotExist:
            logger.error(f"Workflow {workflow_id} not found")
            raise ObjectDoesNotExist(f"Workflow with ID {workflow_id} does not exist")
        except PermissionError:
            raise
        
        # Fetch activities with agent, skill, artifacts, and rules
        activities = list(
            workflow.activities.select_related('agent').prefetch_related('skills', 'rules')
            .prefetch_related(
                'output_artifacts',
                'input_artifacts__artifact',
                'rules',
            )
            .order_by('order')
        )
        logger.info(f"Found {len(activities)} activities in workflow '{workflow.name}'")
        
        if not folder_name:
            folder_name = WorkflowExportService._slugify(workflow.name)
        
        export_path = Path(target_directory) / folder_name
        try:
            export_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created export directory: {export_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {export_path}: {e}")
            raise PermissionError(f"Cannot create directory {export_path}: {e}")
        
        files_created = []
        
        workflow_md = WorkflowExportService._generate_workflow_metadata_md(workflow, len(activities))
        workflow_file = export_path / "_workflow.md"
        workflow_file.write_text(workflow_md, encoding='utf-8')
        files_created.append("_workflow.md")
        logger.info("Created _workflow.md")
        
        slug_prefix = folder_name
        for activity in activities:
            filename, content = WorkflowExportService._generate_activity_md(
                activity, activity.order, slug_prefix
            )
            activity_file = export_path / filename
            activity_file.write_text(content, encoding='utf-8')
            files_created.append(filename)
            logger.info(f"Created {filename}")

        rules_dir, rule_files = WorkflowExportService._export_rules_for_workflow(
            activities, Path(target_directory)
        )
        files_created.extend(rule_files)

        result = {
            'status': 'exported',
            'workflow_id': workflow_id,
            'workflow_name': workflow.name,
            'export_path': str(export_path.absolute()),
            'rules_export_path': str(rules_dir.absolute()) if rules_dir else '',
            'files_created': files_created,
            'rule_files_created': rule_files,
            'message': 'Workflow exported successfully. Edit files locally and use import_workflow_from_local to apply changes.'
        }
        
        logger.info(f"Export completed: {len(files_created)} files created at {export_path}")
        return result
    
    @staticmethod
    def _generate_workflow_metadata_md(workflow, activity_count: int) -> str:
        """Generate _workflow.md content with metadata."""
        from datetime import datetime
        
        playbook = workflow.playbook
        export_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        has_phases = any(a.phase_id for a in workflow.activities.all())
        phase_info = "Uses phases" if has_phases else "No phase organization"
        
        md = f"""# {workflow.name}

**Playbook**: {playbook.name} v{playbook.version} ({playbook.status.capitalize()})
**Workflow ID**: {workflow.id}
**Description**: {workflow.description or 'No description provided'}
**Phase Organization**: {phase_info}
**Total Activities**: {activity_count}
**Export Date**: {export_date}

## Activities

See individual activity files in this directory.

## Editing Instructions

- **Add activity**: Create new file with pattern PREFIX-XX-Name.md
- **Remove activity**: Delete the .md file
- **Reorder**: Rename files to change order numbers
- **Edit content**: Modify description, guidance, dependencies
- **Change phase**: Update the Phase field

After editing, use import_workflow_from_local MCP tool to import changes.
"""
        return md
    
    @staticmethod
    def _generate_activity_md(activity, order: int, slug_prefix: str) -> tuple[str, str]:
        """
        Generate activity markdown file with agent, skill, and artifacts.
        
        :param activity: Activity instance with prefetched agent, skill, artifacts
        :param order: Activity order number
        :param slug_prefix: Prefix for filename
        :return: Tuple of (filename, content)
        """
        slug = WorkflowExportService._slugify(activity.name)
        filename = f"{slug_prefix}-{order:02d}-{slug}.md"
        
        dependencies = []
        if activity.predecessor:
            dependencies.append(f"Predecessor: Activity {activity.predecessor.id} ({activity.predecessor.name})")
        if activity.successor:
            dependencies.append(f"Successor: Activity {activity.successor.id} ({activity.successor.name})")
        
        dependencies_text = "\n".join(dependencies) if dependencies else "None"
        phase_text = activity.phase.name if activity.phase else "None"
        
        # Build agent section (Issue #72)
        if activity.agent:
            agent_text = f"""**Name**: {activity.agent.name}
**Description**: {activity.agent.description if activity.agent.description else 'No description'}"""
        else:
            agent_text = "None"
        
        # Build skill section (Issue #72)
        linked_skills = list(activity.skills.all())
        if linked_skills:
            skill_lines = []
            for skill in linked_skills:
                skill_lines.append(f"**Title**: {skill.title}")
                if skill.capability_domain:
                    skill_lines.append(f"**Capability Domain**: {skill.capability_domain}")
                if skill.technology_stack:
                    skill_lines.append(f"**Technology Stack**: {skill.technology_stack}")
                skill_lines.append("")
            skill_text = "\n".join(skill_lines).strip()
        else:
            skill_text = "None"

        rule_links = list(activity.rules.all())
        if rule_links:
            rules_lines = [f"- **{r.title}** (`{r.slug}`)" for r in sorted(rule_links, key=lambda x: x.slug)]
            rules_text = "\n".join(rules_lines)
        else:
            rules_text = "None"

        # Build artifacts produced section (Issue #72)
        output_artifacts = list(activity.output_artifacts.all())
        if output_artifacts:
            artifacts_produced_lines = []
            for artifact in output_artifacts:
                req_text = "Required" if artifact.is_required else "Optional"
                artifacts_produced_lines.append(
                    f"- **{artifact.name}** ({artifact.type}) - {req_text}"
                )
            artifacts_produced_text = "\n".join(artifacts_produced_lines)
        else:
            artifacts_produced_text = "None"
        
        # Build artifacts consumed section (Issue #72)
        input_artifact_inputs = list(activity.input_artifacts.all())
        if input_artifact_inputs:
            artifacts_consumed_lines = []
            for ai in input_artifact_inputs:
                req_text = "Required" if ai.is_required else "Optional"
                artifacts_consumed_lines.append(
                    f"- **{ai.artifact.name}** ({ai.artifact.type}) - {req_text}"
                )
            artifacts_consumed_text = "\n".join(artifacts_consumed_lines)
        else:
            artifacts_consumed_text = "None"
        
        content = f"""# Activity: {activity.name}

**Activity ID**: {activity.id}
**Order**: {order}
**Phase**: {phase_text}
**Dependencies**: {dependencies_text}

## Description

{activity.name}

## Guidance

{activity.guidance if activity.guidance else 'No guidance provided.'}

## Agent

{agent_text}

## Skill

{skill_text}

## Rules

{rules_text}

## Artifacts Produced

{artifacts_produced_text}

## Artifacts Consumed

{artifacts_consumed_text}

## Notes

No additional notes.
"""
        
        return filename, content
    
    @staticmethod
    def _export_rules_for_workflow(activities, workflows_root: Path):
        """
        Write distinct playbook rules referenced by activities into sibling ``rules/`` folder.

        :returns: Tuple of (rules directory Path or None, list of relative paths created)
        """
        seen = {}
        for activity in activities:
            for rule in activity.rules.all():
                seen[rule.id] = rule
        if not seen:
            logger.info('No rules linked to workflow activities; skipping rules export')
            return None, []

        try:
            rules_parent = workflows_root.resolve().parent
        except OSError:
            rules_parent = workflows_root.parent
        rules_dir = rules_parent / 'rules'
        try:
            rules_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error('Failed to create rules directory %s: %s', rules_dir, e)
            raise PermissionError(f'Cannot create rules directory {rules_dir}: {e}') from e

        rel_created = []
        for rule in sorted(seen.values(), key=lambda r: r.slug):
            fname = f'{rule.slug}.mdc'
            body = WorkflowExportService._format_rule_mdc(rule)
            out = rules_dir / fname
            out.write_text(body, encoding='utf-8')
            rel = f'rules/{fname}'
            rel_created.append(rel)
            logger.info('Exported rule file %s', out)

        return rules_dir, rel_created

    @staticmethod
    def _format_rule_mdc(rule) -> str:
        """Cursor-style .mdc body with YAML front matter."""
        aa = 'true' if rule.always_apply else 'false'
        fm = f'---\nalwaysApply: {aa}\n---\n\n'
        content = rule.content.strip() if rule.content else ''
        return fm + content + ('\n' if content and not content.endswith('\n') else '')

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to slug format."""
        slug = text.replace(' ', '_')
        slug = re.sub(r'[^\w\-]', '', slug)
        slug = re.sub(r'_+', '_', slug)
        slug = slug.strip('_')
        return slug
