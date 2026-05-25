"""
DRF ViewSets for Mimir API.

Maps HTTP endpoints to service layer methods, maintaining 1:1 parity with MCP tools.
"""

import logging
from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from methodology.models import (
    Playbook, Workflow, Activity, Skill, Agent, Artifact,
    ArtifactInput, Phase, Rule
)
from methodology.api.serializers import (
    PlaybookSerializer, PlaybookListSerializer, WorkflowSerializer,
    ActivitySerializer, ActivityListSerializer, SkillSerializer, AgentSerializer,
    ArtifactSerializer, ArtifactInputSerializer, PhaseSerializer,
    RuleSerializer
)
from methodology.api.permissions import IsOwnerOrReadOnly, IsDraftPlaybook
from methodology.services.playbook_service import PlaybookService
from methodology.services.workflow_service import WorkflowService
from methodology.services.activity_service import ActivityService

logger = logging.getLogger(__name__)


def _accessible_playbook_ids(user):
    """
    Return a set of playbook PKs the user may read:
    their own playbooks (any status/visibility) plus public non-draft
    playbooks authored by others.

    Mirrors PlaybookViewSet.get_queryset() so that all resource viewsets
    honour the same access contract (bug #115 fix).
    """
    from django.db.models import Q
    owned_ids = set(
        Playbook.objects.filter(
            Q(author=user) | Q(shared_with_groups__in=user.groups.all())
        ).distinct().values_list("pk", flat=True)
    )
    public_ids = {p.pk for p in PlaybookService.list_public_playbooks(user)}
    return owned_ids | public_ids


class PlaybookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Playbook resource.
    
    Maps to MCP tools: create_playbook, list_playbooks, get_playbook,
    update_playbook, delete_playbook.
    """

    resource_name = "Playbook"
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsDraftPlaybook]
    
    def get_serializer_class(self):
        """Use lightweight serializer for list, full for detail."""
        if self.action == 'list':
            return PlaybookListSerializer
        return PlaybookSerializer
    
    def get_queryset(self):
        """
        Playbooks the user may access: owned, shared via groups, or public (others, non-draft).
        """
        from django.db.models import Q

        user = self.request.user

        owned_or_shared = (
            Playbook.objects.filter(
                Q(author=user) | Q(shared_with_groups__in=user.groups.all())
            )
            .distinct()
            .values_list("pk", flat=True)
        )
        public_ids = [p.pk for p in PlaybookService.list_public_playbooks(user)]
        all_ids = set(owned_or_shared) | set(public_ids)

        queryset = Playbook.objects.filter(pk__in=all_ids).distinct()

        status_filter = self.request.query_params.get('status')
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by('-updated_at')
    
    def create(self, request):
        """
        Create new draft playbook (v0.1).
        
        Maps to: create_playbook MCP tool
        """
        logger.info(f'API: create_playbook called by user={request.user.id}')
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        playbook = PlaybookService.create_playbook(
            name=serializer.validated_data['name'],
            description=serializer.validated_data['description'],
            category=serializer.validated_data.get('category', 'general'),
            author=request.user,
            status='draft',
            visibility=serializer.validated_data.get('visibility', 'private'),
        )

        logger.info(f'API: Created playbook id={playbook.id}, version={playbook.version}')

        response_serializer = self.get_serializer(playbook)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, pk=None, partial=False):
        """
        Update draft playbook (increments version).
        
        Maps to: update_playbook MCP tool
        """
        logger.info(f'API: update_playbook called - id={pk}')
        
        from django.core.exceptions import ValidationError as DjangoValidationError

        playbook = self.get_object()

        serializer = self.get_serializer(playbook, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        old_version = playbook.version
        update_payload = {}
        for field in ('name', 'description', 'category', 'visibility'):
            if field in serializer.validated_data:
                update_payload[field] = serializer.validated_data[field]

        changed = bool(update_payload)
        if changed:
            try:
                playbook = PlaybookService.update_playbook(pk, **update_payload)
            except DjangoValidationError as e:
                from rest_framework.exceptions import ValidationError as DRFValidationError
                raise DRFValidationError(detail=getattr(e, 'message_dict', str(e)))

            playbook.version += Decimal('0.1')
            playbook.save()
            logger.info(f'API: Updated playbook, version {old_version} → {playbook.version}')

        response_serializer = self.get_serializer(playbook)
        return Response(response_serializer.data)
    
    def destroy(self, request, pk=None):
        """
        Delete draft playbook (cascades to workflows/activities).
        
        Maps to: delete_playbook MCP tool
        """
        logger.info(f'API: delete_playbook called - id={pk}')
        
        playbook = self.get_object()
        playbook_name = playbook.name
        workflow_count = playbook.workflows.count()
        
        # Use service layer for cascade delete
        PlaybookService.delete_playbook(pk)
        
        logger.info(f'API: Deleted playbook "{playbook_name}" with {workflow_count} workflows')
        return Response({'deleted': True, 'playbook_id': pk})
    
    @action(detail=True, methods=['put'], url_path='phases/reorder')
    def reorder_phases(self, request, pk=None):
        """
        Reorder phases in draft playbook.
        
        Maps to: reorder_phases MCP tool
        """
        logger.info(f'API: reorder_phases called - playbook_id={pk}')
        
        playbook = self.get_object()
        phase_order = request.data.get('phase_order', [])
        
        if not phase_order:
            return Response(
                {'error': 'phase_order is required', 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Import service here to avoid circular imports
        from methodology.services.phase_service import PhaseService
        
        result = PhaseService.reorder_phases(pk, phase_order)
        
        # Increment playbook version
        old_version = playbook.version
        playbook.version += Decimal('0.1')
        playbook.save()
        
        logger.info(f'API: Reordered {len(phase_order)} phases, version {old_version} → {playbook.version}')
        
        return Response({
            'reordered': True,
            'count': len(phase_order)
        })
    
    @action(detail=True, methods=['put'], url_path='share')
    def share_with_groups(self, request, pk=None):
        """
        Share playbook with groups.
        
        Only owner can share. Replaces existing group sharing.
        """
        logger.info(f'API: share_with_groups called - playbook_id={pk}')
        
        playbook = self.get_object()
        
        # Only owner can share
        if playbook.author != request.user:
            return Response(
                {'error': 'Only the owner can share this playbook', 'code': 'PERMISSION_DENIED'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        group_ids = request.data.get('group_ids', [])
        
        # Import Group model
        from django.contrib.auth.models import Group
        
        # Validate all groups exist
        groups = Group.objects.filter(id__in=group_ids)
        if len(groups) != len(group_ids):
            return Response(
                {'error': 'One or more group IDs are invalid', 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Replace shared groups
        playbook.shared_with_groups.set(groups)
        
        logger.info(f'API: Playbook {pk} shared with {len(group_ids)} groups')
        
        return Response({
            'playbook_id': pk,
            'shared_with_groups': [{'id': g.id, 'name': g.name} for g in groups],
            'count': len(groups)
        })


class WorkflowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Workflow resource.
    
    Maps to MCP tools: create_workflow, list_workflows, get_workflow,
    update_workflow, delete_workflow, export_workflow_to_local,
    import_workflow_from_local, apply_upload_protocol, create_pip_from_protocol.
    """

    resource_name = "Workflow"
    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsDraftPlaybook]
    
    def get_queryset(self):
        """Workflows for playbooks accessible to the current user (owned or public non-draft)."""
        accessible = _accessible_playbook_ids(self.request.user)
        queryset = Workflow.objects.filter(playbook_id__in=accessible)

        playbook_id = self.request.query_params.get('playbook_id')
        if playbook_id:
            queryset = queryset.filter(playbook_id=playbook_id)

        return queryset.order_by('order')
    
    def create(self, request):
        """
        Create workflow in draft playbook.
        
        Maps to: create_workflow MCP tool
        """
        logger.info(f'API: create_workflow called by user={request.user.id}')
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get playbook and verify ownership
        # DRF stores FK relation as source key ('playbook'), fall back to raw request data
        if hasattr(serializer.validated_data.get('playbook'), 'id'):
            playbook_id = serializer.validated_data['playbook'].id
        else:
            playbook_id = request.data.get('playbook_id')
        playbook = get_object_or_404(
            Playbook,
            id=playbook_id,
            author=request.user
        )
        
        # Check draft status
        if playbook.status != 'draft':
            return Response(
                {'error': f'Cannot modify released playbook "{playbook.name}". Use create_pip instead.',
                 'code': 'PERMISSION_DENIED'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create workflow using service (takes playbook object, not playbook_id)
        workflow = WorkflowService.create_workflow(
            playbook=playbook,
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
        )
        
        # Increment parent version
        old_version = playbook.version
        playbook.version += Decimal('0.1')
        playbook.save()
        
        logger.info(f'API: Created workflow id={workflow.id}, parent version {old_version} → {playbook.version}')
        
        response_serializer = self.get_serializer(workflow)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def export(self, request, pk=None):
        """
        Export workflow to markdown files. Read-only — allowed on released playbooks too.

        Maps to: export_workflow_to_local MCP tool
        """
        logger.info(f'API: export_workflow_to_local called - workflow_id={pk}')

        workflow = self.get_object()
        target_directory = request.data.get('target_directory', '.windsurf/workflows')
        folder_name = request.data.get('folder_name')
        
        from methodology.services.workflow_export_service import WorkflowExportService

        try:
            result = WorkflowExportService.export_workflow_to_markdown(
                workflow_id=pk,
                target_directory=target_directory,
                folder_name=folder_name,
            )
        except (PermissionError, OSError) as exc:
            return Response(
                {'error': f'Export to filesystem not supported on hosted server: {exc}',
                 'code': 'NOT_SUPPORTED'},
                status=status.HTTP_501_NOT_IMPLEMENTED
            )
        return Response(result)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def import_workflow(self, request, pk=None):
        """
        Import workflow from markdown files (diff-only; no writes on released playbooks).

        Maps to: import_workflow_from_local MCP tool
        """
        logger.info(f'API: import_workflow_from_local called - workflow_id={pk}')
        
        workflow = self.get_object()
        source_directory = request.data.get('source_directory')
        auto_apply = request.data.get('auto_apply', False)
        
        if not source_directory:
            return Response(
                {'error': 'source_directory is required', 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Import service here to avoid circular imports
        from methodology.services.workflow_import_service import WorkflowImportService
        
        result = WorkflowImportService.import_workflow_from_markdown(
            workflow_id=pk,
            source_directory=source_directory,
        )
        
        return Response(result)
    
    @action(detail=True, methods=['post'], url_path='apply-protocol')
    def apply_protocol(self, request, pk=None):
        """
        Apply upload protocol to draft workflow (workflow_id parsed from the protocol file).

        Maps to: apply_upload_protocol MCP tool.
        The facade calls POST /api/workflows/0/apply-protocol/ where pk=0 is a placeholder;
        the actual workflow is resolved from the protocol file by the service.
        """
        logger.info('API: apply_upload_protocol called (pk=%s — resolved from protocol file)', pk)

        protocol_file = request.data.get('protocol_file')
        if not protocol_file:
            return Response(
                {'error': 'protocol_file is required', 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from methodology.services.workflow_protocol_service import WorkflowProtocolService

        try:
            result = WorkflowProtocolService.apply_upload_protocol(protocol_file)
        except (ValidationError, PermissionError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)
    
    @action(detail=True, methods=['post'], url_path='create-pip')
    def create_pip(self, request, pk=None):
        """
        Create PIP from protocol for released workflow.
        
        Maps to: create_pip_from_protocol MCP tool
        """
        logger.info('API: create_pip_from_protocol called (pk=%s — resolved from protocol file)', pk)

        protocol_file = request.data.get('protocol_file')
        pip_title = request.data.get('pip_title')

        if not protocol_file or not pip_title:
            return Response(
                {'error': 'protocol_file and pip_title are required', 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from methodology.services.pip_service import PIPService

        try:
            result = PIPService.create_pip_from_protocol(
                protocol_file, pip_title, actor=request.user
            )
        except (ValidationError, ValueError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_201_CREATED)


class ActivityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Activity resource.
    
    Maps to MCP tools: create_activity, list_activities, get_activity,
    update_activity, delete_activity, set_predecessor.
    """

    resource_name = "Activity"
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsDraftPlaybook]

    def get_serializer_class(self):
        """Use lightweight list serializer (no guidance) for list action."""
        if self.action == 'list':
            return ActivityListSerializer
        return ActivitySerializer

    def get_queryset(self):
        """Activities for workflows in playbooks accessible to the current user."""
        accessible = _accessible_playbook_ids(self.request.user)
        queryset = Activity.objects.filter(
            workflow__playbook_id__in=accessible
        ).select_related(
            'predecessor', 'agent', 'workflow', 'workflow__playbook'
        ).prefetch_related('skills')

        workflow_id = self.request.query_params.get('workflow_id')
        if workflow_id:
            queryset = queryset.filter(workflow_id=workflow_id)

        return queryset.order_by('order')
    
    def create(self, request):
        """
        Create activity in workflow (draft playbook only).
        
        Maps to: create_activity MCP tool
        """
        logger.info(f'API: create_activity called by user={request.user.id}')
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # workflow_id is now writable via explicit IntegerField on ActivitySerializer
        workflow_id = serializer.validated_data.get('workflow_id') or request.data.get('workflow_id')
        workflow = get_object_or_404(
            Workflow,
            id=workflow_id,
            playbook__author=request.user
        )

        # Check draft status
        if workflow.playbook.status != 'draft':
            return Response(
                {'error': f'Cannot modify released playbook "{workflow.playbook.name}". Use create_pip instead.',
                 'code': 'PERMISSION_DENIED'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Create activity using service (takes workflow object, not workflow_id)
        activity = ActivityService.create_activity(
            workflow=workflow,
            name=serializer.validated_data['name'],
            guidance=serializer.validated_data.get('guidance', ''),
            phase_id=serializer.validated_data.get('phase_id'),
            order=serializer.validated_data.get('order', 1)
        )
        
        # Increment grandparent version
        playbook = workflow.playbook
        old_version = playbook.version
        playbook.version += Decimal('0.1')
        playbook.save()
        
        logger.info(f'API: Created activity id={activity.id}, grandparent version {old_version} → {playbook.version}')
        
        response_serializer = self.get_serializer(activity)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['put'])
    def predecessor(self, request, pk=None):
        """
        Set predecessor dependency.
        
        Maps to: set_predecessor MCP tool
        """
        logger.info(f'API: set_predecessor called - activity_id={pk}')
        
        activity = self.get_object()
        predecessor_id = request.data.get('predecessor_id')
        
        if not predecessor_id:
            return Response(
                {'error': 'predecessor_id is required', 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set predecessor using service
        try:
            from methodology.models import Activity as ActivityModel
            predecessor = ActivityModel.objects.get(pk=predecessor_id)
            ActivityService.set_predecessor(activity, predecessor)
        except ActivityModel.DoesNotExist:
            return Response(
                {'error': 'Predecessor activity not found', 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except (ValueError, ValidationError) as e:
            return Response(
                {'error': str(e), 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Refresh from DB
        activity.refresh_from_db()
        
        response_serializer = self.get_serializer(activity)
        return Response(response_serializer.data)
    
    @action(detail=True, methods=['put', 'delete'])
    def skill(self, request, pk=None):
        """
        Add (PUT) or remove (DELETE) one skill on an activity.

        Maps to: link_skill_to_activity / unlink_skill_from_activity MCP tools
        """
        activity = self.get_object()
        if request.method == 'PUT':
            logger.info(f'API: link_skill_to_activity called - activity_id={pk}')
            skill_id = request.data.get('skill_id')
            if not skill_id:
                return Response(
                    {'error': 'skill_id is required', 'code': 'VALIDATION_ERROR'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                ActivityService.add_activity_skill(activity.id, int(skill_id))
            except ValidationError as e:
                return Response(
                    {'error': str(e), 'code': 'VALIDATION_ERROR'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            activity.refresh_from_db()
            skill_ids = list(activity.skills.values_list('id', flat=True))
            skill = get_object_or_404(Skill, id=skill_id)
            return Response({
                'activity_id': activity.id,
                'skill_id': skill.id,
                'skill_title': skill.title,
                'skill_ids': skill_ids,
            })
        logger.info(f'API: unlink_skill_from_activity called - activity_id={pk}')
        skill_id = request.data.get('skill_id')
        if not skill_id:
            return Response(
                {'error': 'skill_id is required', 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ActivityService.remove_activity_skill(activity.id, int(skill_id))
        activity.refresh_from_db()
        skill_ids = list(activity.skills.values_list('id', flat=True))
        return Response({
            'activity_id': activity.id,
            'skill_id': int(skill_id),
            'skill_ids': skill_ids,
        })

    @action(detail=True, methods=['put'], url_path='skills')
    def skills_bulk(self, request, pk=None):
        """
        Replace all skills on an activity.

        Maps to: set_activity_skills MCP tool
        """
        logger.info(f'API: set_activity_skills called - activity_id={pk}')
        activity = self.get_object()
        skill_ids = request.data.get('skill_ids', [])
        if skill_ids is None:
            skill_ids = []
        try:
            ActivityService.set_activity_skills(activity.id, skill_ids)
        except ValidationError as e:
            return Response(
                {'error': str(e), 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST
            )
        activity.refresh_from_db()
        result_ids = list(activity.skills.values_list('id', flat=True))
        return Response({'activity_id': activity.id, 'skill_ids': result_ids})
    
    @action(detail=True, methods=['put', 'delete'])
    def agent(self, request, pk=None):
        """
        Link (PUT) or unlink (DELETE) agent from activity.
        
        Maps to: link_agent_to_activity / unlink_agent_from_activity MCP tools
        """
        activity = self.get_object()
        if request.method == 'PUT':
            logger.info(f'API: link_agent_to_activity called - activity_id={pk}')
            agent_id = request.data.get('agent_id')
            if not agent_id:
                return Response(
                    {'error': 'agent_id is required', 'code': 'VALIDATION_ERROR'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            agent = get_object_or_404(Agent, id=agent_id)
            if agent.playbook_id != activity.workflow.playbook_id:
                return Response(
                    {'error': 'Cannot link agent from different playbook', 'code': 'CROSS_PLAYBOOK'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            activity.agent = agent
            activity.save()
            return Response({'activity_id': activity.id, 'agent_id': agent.id, 'agent_name': agent.name})
        else:  # DELETE
            logger.info(f'API: unlink_agent_from_activity called - activity_id={pk}')
            activity.agent = None
            activity.save()
            return Response({'activity_id': activity.id, 'agent_id': None})
    
    @action(detail=True, methods=['put'])
    def rules(self, request, pk=None):
        """
        Replace activity's linked rules.
        
        Maps to: set_activity_rules MCP tool
        """
        logger.info(f'API: set_activity_rules called - activity_id={pk}')
        
        activity = self.get_object()
        rule_ids = request.data.get('rule_ids', [])
        
        # Verify all rules exist and are in same playbook
        rules = Rule.objects.filter(id__in=rule_ids)
        for rule in rules:
            if rule.playbook_id != activity.workflow.playbook_id:
                return Response(
                    {'error': 'Cannot link rule from different playbook', 'code': 'CROSS_PLAYBOOK'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Replace rules
        activity.rules.set(rules)
        
        return Response({
            'activity_id': activity.id,
            'rule_ids': list(rule_ids),
            'count': len(rule_ids)
        })


# Continuing with remaining ViewSets in next file due to length...
