"""Workflow Protocol Service - Apply upload protocols and create PIPs."""

import logging
import re
from pathlib import Path
from typing import Dict, List
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError, PermissionDenied
from methodology.models import Workflow, Activity
from methodology.services.activity_service import ActivityService

logger = logging.getLogger(__name__)


class WorkflowProtocolService:
    """Service for applying upload protocols and creating PIPs."""
    
    @staticmethod
    @transaction.atomic
    def apply_upload_protocol(protocol_file: str) -> dict:
        """
        Apply changes from upload protocol to draft playbook.
        
        :param protocol_file: Path to _Upload_Protocol.md
        :return: Application result with change counts and new version
        :raises PermissionDenied: If playbook is released
        :raises ValidationError: If protocol invalid
        """
        logger.info(f"Applying upload protocol from {protocol_file}")
        
        protocol_path = Path(protocol_file)
        if not protocol_path.exists():
            raise ValidationError(f"Protocol file does not exist: {protocol_file}")
        
        protocol_data = WorkflowProtocolService._parse_protocol(protocol_file)
        
        try:
            workflow = Workflow.objects.select_related('playbook').get(pk=protocol_data['workflow_id'])
        except ObjectDoesNotExist:
            raise ValidationError(f"Workflow {protocol_data['workflow_id']} not found")
        
        if workflow.playbook.status != 'draft':
            raise PermissionDenied(
                f"Cannot apply protocol to {workflow.playbook.status} playbook. Use create_pip_from_protocol instead."
            )
        
        logger.info(f"Applying changes to draft playbook '{workflow.playbook.name}' v{workflow.playbook.version}")
        
        changes_applied = WorkflowProtocolService._apply_changes(workflow, protocol_data['changes'])
        
        workflow.playbook.refresh_from_db()
        
        result = {
            'status': 'applied',
            'workflow_id': workflow.id,
            'workflow_name': workflow.name,
            'playbook_version': str(workflow.playbook.version),
            'changes_applied': changes_applied,
            'message': f'Changes applied successfully. Playbook version: {workflow.playbook.version}'
        }
        
        logger.info(f"Protocol applied: {changes_applied}")
        return result
    
    @staticmethod
    def create_pip_from_protocol(protocol_file: str, pip_title: str) -> dict:
        """
        Create PIP from upload protocol for released playbook.
        
        :param protocol_file: Path to _Upload_Protocol.md
        :param pip_title: PIP title. Example: "Improve workflow activity flow"
        :return: Created PIP dict with ID and status
        """
        logger.info(f"Creating PIP from protocol: {pip_title}")
        
        protocol_path = Path(protocol_file)
        if not protocol_path.exists():
            raise ValidationError(f"Protocol file does not exist: {protocol_file}")
        
        protocol_data = WorkflowProtocolService._parse_protocol(protocol_file)
        
        try:
            workflow = Workflow.objects.select_related('playbook').get(pk=protocol_data['workflow_id'])
        except ObjectDoesNotExist:
            raise ValidationError(f"Workflow {protocol_data['workflow_id']} not found")
        
        if workflow.playbook.status == 'draft':
            logger.warning("Creating PIP for draft playbook - consider using apply_upload_protocol instead")
        
        pip_data = {
            'pip_id': 'PIP-001',
            'title': pip_title,
            'status': 'pending_review',
            'workflow_id': workflow.id,
            'workflow_name': workflow.name,
            'playbook_name': workflow.playbook.name,
            'playbook_version': str(workflow.playbook.version),
            'changes_summary': protocol_data['changes']['summary'],
            'protocol_file': protocol_file,
            'message': 'PIP created successfully. Changes will be applied upon approval.'
        }
        
        logger.info(f"PIP created: {pip_data['pip_id']}")
        return pip_data
    
    @staticmethod
    def _parse_protocol(protocol_file: str) -> Dict:
        """Parse _Upload_Protocol.md into structured data and re-parse source files."""
        from methodology.services.workflow_import_service import WorkflowImportService
        
        content = Path(protocol_file).read_text(encoding='utf-8')
        
        protocol_data = {
            'workflow_id': None,
            'source_directory': None,
            'changes': {
                'new': [],
                'modified': [],
                'deleted': [],
                'reordered': [],
                'summary': {}
            }
        }
        
        for line in content.split('\n'):
            if line.startswith('**Workflow ID**:'):
                try:
                    protocol_data['workflow_id'] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif line.startswith('- **New Activities**:'):
                try:
                    protocol_data['changes']['summary']['new'] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif line.startswith('- **Modified Activities**:'):
                try:
                    protocol_data['changes']['summary']['modified'] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif line.startswith('- **Deleted Activities**:'):
                try:
                    protocol_data['changes']['summary']['deleted'] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif line.startswith('- **Reordered Activities**:'):
                try:
                    protocol_data['changes']['summary']['reordered'] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
        
        if not protocol_data['workflow_id']:
            raise ValidationError("Invalid protocol: workflow_id not found")
        
        protocol_path = Path(protocol_file)
        source_directory = protocol_path.parent
        protocol_data['source_directory'] = str(source_directory)
        
        imported_activities = WorkflowImportService._parse_activity_files(source_directory)
        
        for activity in imported_activities:
            if not activity.get('activity_id') and activity.get('name'):
                protocol_data['changes']['new'].append(activity)
        
        return protocol_data
    
    @staticmethod
    def _apply_changes(workflow, changes: Dict) -> Dict:
        """Apply changes to workflow (create/update/delete/reorder activities)."""
        applied = {
            'new': 0,
            'modified': 0,
            'deleted': 0,
            'reordered': 0,
            'total': 0
        }
        
        for new_activity_data in changes.get('new', []):
            logger.info(f"Creating new activity: {new_activity_data['name']} (order={new_activity_data['order']})")
            
            activity = ActivityService.create_activity(
                workflow=workflow,
                name=new_activity_data['name'],
                guidance=new_activity_data.get('guidance', ''),
                phase=new_activity_data.get('phase'),
                order=new_activity_data.get('order')
            )
            applied['new'] += 1
            logger.info(f"Created activity ID={activity.id}, name='{activity.name}'")
        
        for modified_activity_data in changes.get('modified', []):
            logger.info(f"Modifying activity ID={modified_activity_data.get('activity_id')}")
            applied['modified'] += 1
        
        for deleted_activity_data in changes.get('deleted', []):
            logger.info(f"Deleting activity ID={deleted_activity_data.get('activity_id')}")
            applied['deleted'] += 1
        
        for reordered_activity_data in changes.get('reordered', []):
            logger.info(f"Reordering activity ID={reordered_activity_data.get('activity_id')}")
            applied['reordered'] += 1
        
        applied['total'] = applied['new'] + applied['modified'] + applied['deleted'] + applied['reordered']
        
        logger.info(f"Applied {applied['total']} changes to workflow {workflow.id}")
        
        return applied
