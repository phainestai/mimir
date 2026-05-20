"""Workflow Import Service - Import workflows from markdown files with change detection."""

import logging
import re
from pathlib import Path
from typing import Optional, Dict, List
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from methodology.models import Workflow, Activity

logger = logging.getLogger(__name__)


class WorkflowImportService:
    """Service for importing workflows from markdown files."""
    
    @staticmethod
    def import_workflow_from_markdown(workflow_id: int, source_directory: str) -> dict:
        """
        Import workflow from markdown files with change detection.
        
        :param workflow_id: Workflow ID. Example: 42
        :param source_directory: Source directory path. Example: ".windsurf/workflows/FFE"
        :return: Change detection result with protocol data
        :raises ObjectDoesNotExist: If workflow or directory does not exist
        :raises ValidationError: If markdown files invalid
        """
        logger.info(f"Importing workflow {workflow_id} from {source_directory}")
        
        try:
            workflow = Workflow.objects.select_related('playbook').get(pk=workflow_id)
        except ObjectDoesNotExist:
            logger.error(f"Workflow {workflow_id} not found")
            raise ObjectDoesNotExist(f"Workflow with ID {workflow_id} does not exist")
        
        source_path = Path(source_directory)
        if not source_path.exists():
            raise ValidationError(f"Source directory does not exist: {source_directory}")
        
        abbreviation = source_path.name
        if abbreviation and abbreviation != workflow.abbreviation:
            logger.info(f"Updating workflow abbreviation from '{workflow.abbreviation}' to '{abbreviation}'")
            workflow.abbreviation = abbreviation
            workflow.save()
        
        current_activities = list(workflow.activities.all().order_by('order'))
        logger.info(f"Current workflow has {len(current_activities)} activities")
        
        imported_activities = WorkflowImportService._parse_activity_files(source_path)
        logger.info(f"Found {len(imported_activities)} activity files to import")
        
        changes = WorkflowImportService._detect_changes(current_activities, imported_activities)
        logger.info(f"Detected changes: {changes['summary']}")
        
        protocol_content = WorkflowImportService._generate_upload_protocol(
            changes, workflow, workflow.playbook
        )
        
        protocol_file = source_path / '_Upload_Protocol.md'
        protocol_file.write_text(protocol_content, encoding='utf-8')
        logger.info(f"Generated upload protocol at {protocol_file}")
        
        result = {
            'status': 'changes_detected',
            'workflow_id': workflow_id,
            'workflow_name': workflow.name,
            'playbook_status': workflow.playbook.status,
            'changes_count': changes['summary']['total'],
            'changes_summary': changes['summary'],
            'protocol_file': str(protocol_file.absolute()),
            'message': 'Changes detected. Review _Upload_Protocol.md and use apply_upload_protocol or create_pip_from_protocol.'
        }
        
        return result
    
    @staticmethod
    def _parse_activity_files(source_path: Path) -> List[Dict]:
        """Parse all activity markdown files in directory."""
        activities = []
        
        for md_file in sorted(source_path.glob('*.md')):
            if md_file.name in ['_workflow.md', '_Upload_Protocol.md']:
                continue
            
            try:
                activity_data = WorkflowImportService._parse_activity_md(md_file)
                activities.append(activity_data)
                logger.debug(f"Parsed {md_file.name}: {activity_data['name']}")
            except Exception as e:
                logger.warning(f"Failed to parse {md_file.name}: {e}")
        
        return activities
    
    @staticmethod
    def _parse_activity_md(filepath: Path) -> Dict:
        """Parse activity markdown file into dict."""
        content = filepath.read_text(encoding='utf-8')
        
        activity_data = {
            'filename': filepath.name,
            'name': None,
            'activity_id': None,
            'order': None,
            'phase': None,
            'guidance': None,
            'dependencies': []
        }
        
        lines = content.split('\n')
        current_section = None
        guidance_lines = []
        
        for line in lines:
            if line.startswith('# Activity:'):
                activity_data['name'] = line.replace('# Activity:', '').strip()
            elif line.startswith('**Activity ID**:'):
                try:
                    activity_data['activity_id'] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif line.startswith('**Order**:'):
                try:
                    activity_data['order'] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif line.startswith('**Phase**:'):
                phase = line.split(':')[1].strip()
                activity_data['phase'] = None if phase == 'None' else phase
            elif line.startswith('**Dependencies**:'):
                deps_text = line.split(':')[1].strip()
                if deps_text != 'None':
                    activity_data['dependencies'].append(deps_text)
            elif line.startswith('## Guidance'):
                current_section = 'guidance'
            elif line.startswith('##') or line.startswith('---'):
                current_section = None
            elif current_section == 'guidance':
                guidance_lines.append(line)

        raw_guidance = '\n'.join(guidance_lines).strip()
        activity_data['guidance'] = '' if raw_guidance == 'No guidance provided.' else raw_guidance
        
        return activity_data
    
    @staticmethod
    def _detect_changes(current_activities: List, imported_activities: List[Dict]) -> Dict:
        """Detect changes between current and imported activities."""
        changes = {
            'new': [],
            'modified': [],
            'deleted': [],
            'reordered': [],
            'summary': {'new': 0, 'modified': 0, 'deleted': 0, 'reordered': 0, 'total': 0}
        }
        
        current_by_id = {a.id: a for a in current_activities}
        imported_by_id = {a['activity_id']: a for a in imported_activities if a['activity_id']}
        
        for imported in imported_activities:
            if not imported['activity_id']:
                changes['new'].append(imported)
                changes['summary']['new'] += 1
            elif imported['activity_id'] in current_by_id:
                current = current_by_id[imported['activity_id']]
                
                if imported['order'] != current.order:
                    changes['reordered'].append({
                        'activity_id': imported['activity_id'],
                        'name': imported['name'],
                        'old_order': current.order,
                        'new_order': imported['order']
                    })
                    changes['summary']['reordered'] += 1
                
                current_phase_name = current.phase.name if current.phase else None
                imported_guidance = (imported['guidance'] or '').strip()
                current_guidance = (current.guidance or '').strip()
                if (imported['name'] != current.name or
                        imported_guidance != current_guidance or
                        imported['phase'] != current_phase_name):
                    changes['modified'].append({
                        'activity_id': imported['activity_id'],
                        'name': imported['name'],
                        'changes': []
                    })
                    changes['summary']['modified'] += 1
        
        for current in current_activities:
            if current.id not in imported_by_id:
                changes['deleted'].append({
                    'activity_id': current.id,
                    'name': current.name,
                    'order': current.order
                })
                changes['summary']['deleted'] += 1
        
        changes['summary']['total'] = (
            changes['summary']['new'] + 
            changes['summary']['modified'] + 
            changes['summary']['deleted'] + 
            changes['summary']['reordered']
        )
        
        return changes
    
    @staticmethod
    def _generate_upload_protocol(changes: Dict, workflow, playbook) -> str:
        """Generate _Upload_Protocol.md content."""
        from datetime import datetime
        
        protocol_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        
        protocol = f"""# Upload Protocol for {workflow.name}

**Generated**: {protocol_date}
**Workflow ID**: {workflow.id}
**Playbook**: {playbook.name} v{playbook.version} ({playbook.status})

## Change Summary

- **New Activities**: {changes['summary']['new']}
- **Modified Activities**: {changes['summary']['modified']}
- **Deleted Activities**: {changes['summary']['deleted']}
- **Reordered Activities**: {changes['summary']['reordered']}
- **Total Changes**: {changes['summary']['total']}

## Detailed Changes

"""
        
        if changes['new']:
            protocol += "### New Activities\n\n"
            for activity in changes['new']:
                protocol += f"- **{activity['name']}** (Order: {activity['order']}, Phase: {activity['phase'] or 'None'})\n"
                protocol += f"  - **Rationale**: [AI to fill: Why this activity is needed]\n\n"
        
        if changes['modified']:
            protocol += "### Modified Activities\n\n"
            for activity in changes['modified']:
                protocol += f"- **{activity['name']}** (ID: {activity['activity_id']})\n"
                protocol += f"  - **Rationale**: [AI to fill: What changed and why]\n\n"
        
        if changes['deleted']:
            protocol += "### Deleted Activities\n\n"
            for activity in changes['deleted']:
                protocol += f"- **{activity['name']}** (ID: {activity['activity_id']}, Order: {activity['order']})\n"
                protocol += f"  - **Rationale**: [AI to fill: Why this activity is no longer needed]\n\n"
        
        if changes['reordered']:
            protocol += "### Reordered Activities\n\n"
            for activity in changes['reordered']:
                protocol += f"- **{activity['name']}** (ID: {activity['activity_id']}): Order {activity['old_order']} → {activity['new_order']}\n"
                protocol += f"  - **Rationale**: [AI to fill: Why this reordering improves the workflow]\n\n"
        
        protocol += """
## Approval Options

- **Apply Immediately** (Draft playbooks only): Use `apply_upload_protocol` MCP tool
- **Submit as PIP** (Released playbooks): Use `create_pip_from_protocol` MCP tool
- **Cancel**: Delete this protocol file

## Instructions for AI

1. Fill in all [AI to fill] rationale sections above
2. Explain clearly what changed and why it improves the workflow
3. User will review and approve/edit rationales
4. After approval, call appropriate MCP tool to apply changes
"""
        
        return protocol
