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

from methodology.models import (
    Playbook, Workflow, Activity, Skill, Agent, Artifact,
    ArtifactInput, Phase, Rule
)
from methodology.api.serializers import (
    PlaybookSerializer, PlaybookListSerializer, WorkflowSerializer,
    ActivitySerializer, SkillSerializer, AgentSerializer,
    ArtifactSerializer, ArtifactInputSerializer, PhaseSerializer,
    RuleSerializer
)
from methodology.api.permissions import IsOwnerOrReadOnly, IsDraftPlaybook
from methodology.services.playbook_service import PlaybookService
from methodology.services.workflow_service import WorkflowService
from methodology.services.activity_service import ActivityService

logger = logging.getLogger(__name__)


class PlaybookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Playbook resource.
    
    Maps to MCP tools: create_playbook, list_playbooks, get_playbook,
    update_playbook, delete_playbook.
    """
    
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsDraftPlaybook]
    
    def get_serializer_class(self):
        """Use lightweight serializer for list, full for detail."""
        if self.action == 'list':
            return PlaybookListSerializer
        return PlaybookSerializer
    
    def get_queryset(self):
        """
        Get playbooks owned by current user.
        
        Phase 4: Will add group-based filtering for shared playbooks.
        """
        queryset = Playbook.objects.filter(author=self.request.user)
        
        # Filter by status if provided
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
        
        # Create playbook with current user as author
        playbook = Playbook.objects.create(
            author=request.user,
            name=serializer.validated_data['name'],
            description=serializer.validated_data['description'],
            category=serializer.validated_data.get('category', 'general'),
            status='draft',
            version=Decimal('0.1')
        )
        
        logger.info(f'API: Created playbook id={playbook.id}, version={playbook.version}')
        
        response_serializer = self.get_serializer(playbook)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        """
        Update draft playbook (increments version).
        
        Maps to: update_playbook MCP tool
        """
        logger.info(f'API: update_playbook called - id={pk}')
        
        playbook = self.get_object()
        
        # Permission check handled by IsDraftPlaybook permission class
        serializer = self.get_serializer(playbook, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Track if any changes made
        old_version = playbook.version
        changed = False
        
        for field in ['name', 'description', 'category']:
            if field in serializer.validated_data:
                setattr(playbook, field, serializer.validated_data[field])
                changed = True
        
        if changed:
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
        return Response({'deleted': True, 'playbook_id': pk}, status=status.HTTP_204_NO_CONTENT)


class WorkflowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Workflow resource.
    
    Maps to MCP tools: create_workflow, list_workflows, get_workflow,
    update_workflow, delete_workflow.
    """
    
    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsDraftPlaybook]
    
    def get_queryset(self):
        """Get workflows for playbooks owned by current user."""
        queryset = Workflow.objects.filter(playbook__author=self.request.user)
        
        # Filter by playbook_id if provided
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
        playbook = get_object_or_404(
            Playbook,
            id=serializer.validated_data['playbook_id'],
            author=request.user
        )
        
        # Check draft status
        if playbook.status != 'draft':
            return Response(
                {'error': f'Cannot modify released playbook "{playbook.name}". Use create_pip instead.',
                 'code': 'PERMISSION_DENIED'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create workflow using service
        workflow = WorkflowService.create_workflow(
            playbook_id=playbook.id,
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            abbreviation=serializer.validated_data.get('abbreviation')
        )
        
        # Increment parent version
        old_version = playbook.version
        playbook.version += Decimal('0.1')
        playbook.save()
        
        logger.info(f'API: Created workflow id={workflow.id}, parent version {old_version} → {playbook.version}')
        
        response_serializer = self.get_serializer(workflow)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ActivityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Activity resource.
    
    Maps to MCP tools: create_activity, list_activities, get_activity,
    update_activity, delete_activity, set_predecessor.
    """
    
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsDraftPlaybook]
    
    def get_queryset(self):
        """Get activities for workflows owned by current user."""
        queryset = Activity.objects.filter(workflow__playbook__author=self.request.user)
        
        # Filter by workflow_id if provided
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
        
        # Get workflow and verify ownership
        workflow = get_object_or_404(
            Workflow,
            id=serializer.validated_data['workflow_id'],
            playbook__author=request.user
        )
        
        # Check draft status
        if workflow.playbook.status != 'draft':
            return Response(
                {'error': f'Cannot modify released playbook "{workflow.playbook.name}". Use create_pip instead.',
                 'code': 'PERMISSION_DENIED'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create activity using service
        activity = ActivityService.create_activity(
            workflow_id=workflow.id,
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
            ActivityService.set_predecessor(activity.id, predecessor_id)
        except ValueError as e:
            return Response(
                {'error': str(e), 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Refresh from DB
        activity.refresh_from_db()
        
        response_serializer = self.get_serializer(activity)
        return Response(response_serializer.data)
    
    @action(detail=True, methods=['put'])
    def skill(self, request, pk=None):
        """
        Link skill to activity.
        
        Maps to: link_skill_to_activity MCP tool
        """
        logger.info(f'API: link_skill_to_activity called - activity_id={pk}')
        
        activity = self.get_object()
        skill_id = request.data.get('skill_id')
        
        if not skill_id:
            return Response(
                {'error': 'skill_id is required', 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify skill exists and is in same playbook
        skill = get_object_or_404(Skill, id=skill_id)
        if skill.playbook_id != activity.workflow.playbook_id:
            return Response(
                {'error': 'Cannot link skill from different playbook', 'code': 'CROSS_PLAYBOOK'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        activity.skill = skill
        activity.save()
        
        return Response({
            'activity_id': activity.id,
            'skill_id': skill.id,
            'skill_title': skill.title
        })
    
    @action(detail=True, methods=['delete'])
    def skill(self, request, pk=None):
        """
        Unlink skill from activity.
        
        Maps to: unlink_skill_from_activity MCP tool
        """
        logger.info(f'API: unlink_skill_from_activity called - activity_id={pk}')
        
        activity = self.get_object()
        activity.skill = None
        activity.save()
        
        return Response({'activity_id': activity.id, 'skill_id': None})
    
    @action(detail=True, methods=['put'])
    def agent(self, request, pk=None):
        """
        Link agent to activity.
        
        Maps to: link_agent_to_activity MCP tool
        """
        logger.info(f'API: link_agent_to_activity called - activity_id={pk}')
        
        activity = self.get_object()
        agent_id = request.data.get('agent_id')
        
        if not agent_id:
            return Response(
                {'error': 'agent_id is required', 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify agent exists and is in same playbook
        agent = get_object_or_404(Agent, id=agent_id)
        if agent.playbook_id != activity.workflow.playbook_id:
            return Response(
                {'error': 'Cannot link agent from different playbook', 'code': 'CROSS_PLAYBOOK'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        activity.agent = agent
        activity.save()
        
        return Response({
            'activity_id': activity.id,
            'agent_id': agent.id,
            'agent_name': agent.name
        })
    
    @action(detail=True, methods=['delete'])
    def agent(self, request, pk=None):
        """
        Unlink agent from activity.
        
        Maps to: unlink_agent_from_activity MCP tool
        """
        logger.info(f'API: unlink_agent_from_activity called - activity_id={pk}')
        
        activity = self.get_object()
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
