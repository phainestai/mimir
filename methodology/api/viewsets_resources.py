"""
DRF ViewSets for resource models (Skills, Agents, Artifacts, Phases, Rules).

Continuation of viewsets.py for remaining resources.
"""

import logging
from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from methodology.models import (
    Playbook, Skill, Agent, Artifact, ArtifactInput, Phase, Rule
)
from methodology.api.serializers import (
    SkillSerializer, AgentSerializer, ArtifactSerializer,
    ArtifactInputSerializer, PhaseSerializer, RuleSerializer
)
from methodology.api.permissions import IsOwnerOrReadOnly, IsDraftPlaybook

logger = logging.getLogger(__name__)


class SkillViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Skill resource.
    
    Maps to MCP tools: create_skill, list_skills, get_skill,
    update_skill, delete_skill.
    """
    
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsDraftPlaybook]
    
    def get_queryset(self):
        """Get skills for playbooks owned by current user."""
        queryset = Skill.objects.filter(playbook__author=self.request.user)
        
        # Filter by playbook_id if provided
        playbook_id = self.request.query_params.get('playbook_id')
        if playbook_id:
            queryset = queryset.filter(playbook_id=playbook_id)
        
        # Filter by domain if provided
        domain = self.request.query_params.get('domain')
        if domain:
            queryset = queryset.filter(capability_domain=domain)
        
        # Filter by stack if provided
        stack = self.request.query_params.get('stack')
        if stack:
            queryset = queryset.filter(technology_stack=stack)
        
        # Search if provided
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        return queryset.order_by('title')


class AgentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Agent resource.
    
    Maps to MCP tools: create_agent, list_agents, get_agent,
    update_agent, delete_agent.
    """
    
    serializer_class = AgentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsDraftPlaybook]
    
    def get_queryset(self):
        """Get agents for playbooks owned by current user."""
        queryset = Agent.objects.filter(playbook__author=self.request.user)
        
        # Filter by playbook_id if provided
        playbook_id = self.request.query_params.get('playbook_id')
        if playbook_id:
            queryset = queryset.filter(playbook_id=playbook_id)
        
        # Search if provided
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by('name')


class ArtifactViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Artifact resource.
    
    Maps to MCP tools: create_artifact, list_artifacts, get_artifact,
    update_artifact, delete_artifact, link_artifact_to_activity.
    """
    
    serializer_class = ArtifactSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsDraftPlaybook]
    
    def get_queryset(self):
        """Get artifacts for playbooks owned by current user."""
        queryset = Artifact.objects.filter(playbook__author=self.request.user)
        
        # Filter by playbook_id if provided
        playbook_id = self.request.query_params.get('playbook_id')
        if playbook_id:
            queryset = queryset.filter(playbook_id=playbook_id)
        
        # Filter by type if provided
        type_filter = self.request.query_params.get('type')
        if type_filter:
            queryset = queryset.filter(type=type_filter)
        
        # Filter by required if provided
        required_filter = self.request.query_params.get('required')
        if required_filter == 'true':
            queryset = queryset.filter(is_required=True)
        elif required_filter == 'false':
            queryset = queryset.filter(is_required=False)
        
        # Search if provided
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by('name')
    
    @action(detail=True, methods=['post'])
    def consumers(self, request, pk=None):
        """
        Link artifact as input to activity.
        
        Maps to: link_artifact_to_activity MCP tool
        """
        logger.info(f'API: link_artifact_to_activity called - artifact_id={pk}')
        
        artifact = self.get_object()
        activity_id = request.data.get('activity_id')
        is_required = request.data.get('is_required', True)
        
        if not activity_id:
            return Response(
                {'error': 'activity_id is required', 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create artifact input link
        artifact_input = ArtifactInput.objects.create(
            artifact=artifact,
            activity_id=activity_id,
            is_required=is_required
        )
        
        serializer = ArtifactInputSerializer(artifact_input)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ArtifactInputViewSet(viewsets.ViewSet):
    """
    ViewSet for ArtifactInput (artifact-to-activity links).
    
    Maps to MCP tool: unlink_artifact_from_activity.
    """
    
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsDraftPlaybook]
    
    def destroy(self, request, pk=None):
        """
        Unlink artifact from activity.
        
        Maps to: unlink_artifact_from_activity MCP tool
        """
        logger.info(f'API: unlink_artifact_from_activity called - artifact_input_id={pk}')
        
        artifact_input = get_object_or_404(
            ArtifactInput,
            id=pk,
            artifact__playbook__author=request.user
        )
        
        artifact_input.delete()
        
        return Response({'deleted': True})


class PhaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Phase resource.
    
    Maps to MCP tools: create_phase, list_phases, get_phase,
    update_phase, delete_phase, reorder_phases.
    """
    
    serializer_class = PhaseSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsDraftPlaybook]
    
    def get_queryset(self):
        """Get phases for playbooks owned by current user."""
        queryset = Phase.objects.filter(playbook__author=self.request.user)
        
        # Filter by playbook_id if provided
        playbook_id = self.request.query_params.get('playbook_id')
        if playbook_id:
            queryset = queryset.filter(playbook_id=playbook_id)
        
        return queryset.order_by('order')


class RuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Rule resource.
    
    Maps to MCP tools: create_rule, list_rules, get_rule,
    update_rule, delete_rule.
    """
    
    serializer_class = RuleSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsDraftPlaybook]
    
    def get_queryset(self):
        """Get rules for playbooks owned by current user."""
        queryset = Rule.objects.filter(playbook__author=self.request.user)
        
        # Filter by playbook_id if provided
        playbook_id = self.request.query_params.get('playbook_id')
        if playbook_id:
            queryset = queryset.filter(playbook_id=playbook_id)
        
        # Search if provided
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        # Filter unlinked only if provided
        unlinked_only = self.request.query_params.get('unlinked_only')
        if unlinked_only == 'true':
            queryset = queryset.filter(activities__isnull=True)
        
        return queryset.order_by('title')
