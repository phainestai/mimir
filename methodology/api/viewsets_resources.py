"""
DRF ViewSets for resource models (Skills, Agents, Artifacts, Phases, Rules, PIPs).

Continuation of viewsets.py for remaining resources.
"""

import logging
from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.core.exceptions import ValidationError

from methodology.models import (
    Playbook, Skill, Agent, Artifact, ArtifactInput, Phase, Rule,
    ProcessImprovementProposal, PipChange, Team, JoinRequest
)
from methodology.api.serializers import (
    SkillSerializer, AgentSerializer, ArtifactSerializer,
    ArtifactInputSerializer, PhaseSerializer, RuleSerializer,
    PIPSerializer, PIPListSerializer, TeamSerializer, TeamListSerializer,
    JoinRequestSerializer
)
from methodology.api.permissions import IsOwnerOrReadOnly, IsDraftPlaybook
from methodology.api.viewsets import _accessible_playbook_ids

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
        """Skills for playbooks accessible to the current user (owned or public non-draft)."""
        accessible = _accessible_playbook_ids(self.request.user)
        queryset = Skill.objects.filter(playbook_id__in=accessible)

        playbook_id = self.request.query_params.get('playbook_id')
        if playbook_id:
            queryset = queryset.filter(playbook_id=playbook_id)

        domain = self.request.query_params.get('domain')
        if domain:
            queryset = queryset.filter(capability_domain=domain)

        stack = self.request.query_params.get('stack')
        if stack:
            queryset = queryset.filter(technology_stack=stack)

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
        """Agents for playbooks accessible to the current user (owned or public non-draft)."""
        accessible = _accessible_playbook_ids(self.request.user)
        queryset = Agent.objects.filter(playbook_id__in=accessible)

        playbook_id = self.request.query_params.get('playbook_id')
        if playbook_id:
            queryset = queryset.filter(playbook_id=playbook_id)

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
        """Artifacts for playbooks accessible to the current user (owned or public non-draft)."""
        accessible = _accessible_playbook_ids(self.request.user)
        queryset = Artifact.objects.filter(playbook_id__in=accessible)

        playbook_id = self.request.query_params.get('playbook_id')
        if playbook_id:
            queryset = queryset.filter(playbook_id=playbook_id)

        type_filter = self.request.query_params.get('type')
        if type_filter:
            queryset = queryset.filter(type=type_filter)

        required_filter = self.request.query_params.get('required')
        if required_filter == 'true':
            queryset = queryset.filter(is_required=True)
        elif required_filter == 'false':
            queryset = queryset.filter(is_required=False)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by('name')

    def create(self, request):
        """
        Create artifact via service, catching model-level ValidationError.

        Maps to: create_artifact MCP tool
        """
        from django.core.exceptions import ValidationError as DjangoValidationError

        logger.info('API: create_artifact user=%s data=%s', request.user.pk, request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            artifact = serializer.save()
        except DjangoValidationError as exc:
            return Response(
                {'error': exc.message_dict if hasattr(exc, 'message_dict') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(ArtifactSerializer(artifact).data, status=status.HTTP_201_CREATED)
    
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

    resource_name = "Phase"
    serializer_class = PhaseSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsDraftPlaybook]

    def get_queryset(self):
        """Phases for playbooks accessible to the current user (owned or public non-draft)."""
        accessible = _accessible_playbook_ids(self.request.user)
        queryset = Phase.objects.filter(playbook_id__in=accessible)

        playbook_id = self.request.query_params.get('playbook_id')
        if playbook_id:
            queryset = queryset.filter(playbook_id=playbook_id)

        return queryset.order_by('order')

    def create(self, request):
        """
        Create a phase via PhaseService (auto-increments order, enforces ownership).

        Maps to: create_phase MCP tool
        """
        from methodology.services.phase_service import PhaseService

        logger.info('API: create_phase user=%s data=%s', request.user.pk, request.data)
        try:
            phase = PhaseService.create_phase(
                playbook_id=int(request.data['playbook_id']),
                name=request.data['name'],
                description=request.data.get('description', ''),
                order=request.data.get('order'),
                user=request.user,
            )
        except (ValidationError, KeyError, TypeError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PhaseSerializer(phase).data, status=status.HTTP_201_CREATED)


class RuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Rule resource.

    Maps to MCP tools: create_rule, list_rules, get_rule,
    update_rule, delete_rule.
    """

    serializer_class = RuleSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsDraftPlaybook]
    resource_name = "Rule"

    def get_queryset(self):
        """Rules for playbooks accessible to the current user (owned or public non-draft)."""
        accessible = _accessible_playbook_ids(self.request.user)
        queryset = Rule.objects.filter(playbook_id__in=accessible)

        playbook_id = self.request.query_params.get('playbook_id')
        if playbook_id:
            queryset = queryset.filter(playbook_id=playbook_id)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)

        unlinked_only = self.request.query_params.get('unlinked_only')
        if unlinked_only == 'true':
            queryset = queryset.filter(activities__isnull=True)

        return queryset.order_by('title')

    def create(self, request, *args, **kwargs):
        """Create rule, delegating slug generation to RuleService."""
        from methodology.services.rule_service import RuleService
        from methodology.services.playbook_service import PlaybookService

        playbook_id = request.data.get('playbook_id')
        title = request.data.get('title', '')
        content = request.data.get('content', '')
        slug = request.data.get('slug', '')
        always_apply = request.data.get('always_apply', True)

        logger.info(
            "RuleViewSet.create: playbook_id=%s title=%r slug=%r user=%s",
            playbook_id, title, slug, request.user,
        )
        try:
            playbook = PlaybookService.get_playbook(int(playbook_id), user=request.user)
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rule = RuleService.create_rule(
                playbook=playbook,
                title=title,
                content=content,
                slug=slug,
                always_apply=always_apply,
            )
        except ValidationError as exc:
            return Response({'detail': exc.messages}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(rule)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PIPViewSet(viewsets.GenericViewSet):
    """
    ViewSet for Process Improvement Proposals (PIPs).

    Maps to MCP tools: list_pips, get_pip, create_pip, add_pip_change,
    remove_pip_change, submit_pip, cancel_pip, preview_pip_diff.
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return PIPListSerializer
        return PIPSerializer

    def get_queryset(self):
        from methodology.services.pip_service import PIPService
        scope = self.request.query_params.get('scope', 'mine')
        status_codes = self.request.query_params.get('status_codes', '')
        playbook_id = self.request.query_params.get('playbook_id')
        status_list = [s.strip() for s in status_codes.split(',') if s.strip()] if status_codes else None
        try:
            return PIPService.list_queryset_for_user(
                actor=self.request.user,
                scope=scope,
                status_filters=status_list,
                playbook_id=int(playbook_id) if playbook_id else None,
            )
        except PermissionError as exc:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(str(exc)) from exc

    def list(self, request):
        """List PIPs for current user (staff may use scope=all)."""
        logger.info(
            "API: list_pips user=%s scope=%s",
            request.user.pk, request.query_params.get('scope', 'mine')
        )
        qs = self.get_queryset()
        serializer = PIPListSerializer(qs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Get a single PIP with nested changes."""
        logger.info("API: get_pip user=%s pip=%s", request.user.pk, pk)
        from methodology.services.pip_service import PIPService
        try:
            pip = PIPService.get_pip(int(pk), request.user)
        except ProcessImprovementProposal.DoesNotExist:
            return Response({"error": f"PIP {pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        serializer = PIPSerializer(pip)
        return Response(serializer.data)

    def create(self, request):
        """Create a Draft PIP targeting a Released playbook."""
        logger.info("API: create_pip user=%s data=%s", request.user.pk, request.data)
        from methodology.services.pip_service import PIPService
        try:
            pip = PIPService.create_draft_for_playbook(
                actor=request.user,
                playbook_id=int(request.data['playbook_id']),
                title=request.data['title'],
                summary=request.data.get('summary', ''),
            )
        except (ValidationError, KeyError, ValueError) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        refreshed = PIPService.get_pip(pip.pk, request.user)
        return Response(PIPSerializer(refreshed).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='changes')
    def add_change(self, request, pk=None):
        """Add a change row to a Draft PIP."""
        logger.info("API: add_pip_change user=%s pip=%s", request.user.pk, pk)
        from methodology.services.pip_service import PIPService
        try:
            pip = PIPService.get_pip(int(pk), request.user)
            change = PIPService.add_change(
                actor=request.user,
                pip=pip,
                change_type=request.data['change_type'],
                entity_type=request.data.get('entity_type', ''),
                name=request.data.get('name', ''),
                content=request.data.get('content', ''),
                target_id=request.data.get('target_id'),
                parent_workflow_id=request.data.get('parent_workflow_id'),
                parent_workflow_ref=request.data.get('parent_workflow_ref', ''),
                insert_after_activity_id=request.data.get('insert_after_activity_id'),
                insert_after_activity_ref=request.data.get('insert_after_activity_ref', ''),
                phase_ref=request.data.get('phase_ref', ''),
                produced_by_activity_ref=request.data.get('produced_by_activity_ref', ''),
                artifact_type=request.data.get('artifact_type', ''),
                artifact_is_required=bool(request.data.get('artifact_is_required', False)),
                append_to_playbook_end=bool(request.data.get('append_to_playbook_end', False)),
                internal_ref=request.data.get('internal_ref', ''),
                relationship_type=request.data.get('relationship_type', ''),
                source_entity_ref=request.data.get('source_entity_ref', ''),
                target_entity_ref=request.data.get('target_entity_ref', ''),
            )
        except ProcessImprovementProposal.DoesNotExist:
            return Response({"error": f"PIP {pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except (ValidationError, KeyError, ValueError) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"change_id": change.pk}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'changes/(?P<change_id>[0-9]+)')
    def remove_change(self, request, pk=None, change_id=None):
        """Remove a change row from a Draft PIP."""
        logger.info("API: remove_pip_change user=%s pip=%s change=%s", request.user.pk, pk, change_id)
        from methodology.services.pip_service import PIPService
        try:
            pip = PIPService.get_pip(int(pk), request.user)
            PIPService.remove_change(actor=request.user, pip=pip, change_id=int(change_id))
        except ProcessImprovementProposal.DoesNotExist:
            return Response({"error": f"PIP {pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except (ValidationError, ValueError) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"removed": True, "change_id": int(change_id)})

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        """Submit a Draft PIP for Galdr review."""
        logger.info("API: submit_pip user=%s pip=%s", request.user.pk, pk)
        from methodology.services.pip_service import PIPService
        try:
            pip = PIPService.get_pip(int(pk), request.user)
            PIPService.submit_for_review(actor=request.user, pip=pip)
        except ProcessImprovementProposal.DoesNotExist:
            return Response({"error": f"PIP {pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except (ValidationError, ValueError) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        updated = PIPService.get_pip(int(pk), request.user)
        return Response(PIPSerializer(updated).data)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """Withdraw / cancel a PIP (owner only)."""
        logger.info("API: cancel_pip user=%s pip=%s", request.user.pk, pk)
        from methodology.services.pip_service import PIPService
        try:
            pip = PIPService.get_pip(int(pk), request.user)
            PIPService.cancel_pip(pip, request.user)
        except ProcessImprovementProposal.DoesNotExist:
            return Response({"error": f"PIP {pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except (ValidationError, ValueError) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"cancelled": True, "pip_id": int(pk)})

    @action(detail=True, methods=['get'], url_path='preview')
    def preview(self, request, pk=None):
        """Return preview diff rows for a PIP."""
        logger.info("API: preview_pip_diff user=%s pip=%s", request.user.pk, pk)
        from methodology.services.pip_service import PIPService
        try:
            pip = PIPService.get_pip(int(pk), request.user)
            rows = PIPService.summarize_preview_rows(pip)
        except ProcessImprovementProposal.DoesNotExist:
            return Response({"error": f"PIP {pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        return Response({"pip_id": int(pk), "rows": rows})


class TeamViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Team resource.
    
    Maps to MCP tools: list_teams, get_team, create_team,
    move_playbook_to_team, move_playbook_from_team, invite_to_team, manage_team_invite.
    """
    
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Teams visible to the current user (public + member teams)."""
        from methodology.services.team_service import TeamService
        service = TeamService()
        return service.get_teams_visible_to(self.request.user)
    
    def get_serializer_class(self):
        """Use lightweight serializer for list view."""
        if self.action == 'list':
            return TeamListSerializer
        return TeamSerializer
    
    def create(self, request):
        """Create a new team. Caller becomes admin."""
        logger.info(f'API: create_team user={request.user.pk}')
        from methodology.services.team_service import TeamService
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            service = TeamService()
            team = service.create_team(
                user=request.user,
                name=serializer.validated_data['name'],
                description=serializer.validated_data.get('description', ''),
                visibility=serializer.validated_data.get('visibility', Team.VISIBILITY_PUBLIC),
                join_policy=serializer.validated_data.get('join_policy', Team.JOIN_POLICY_AUTO),
                category=serializer.validated_data.get('category', 'Engineering'),
            )
        except ValidationError as exc:
            return Response(
                {'error': exc.message_dict if hasattr(exc, 'message_dict') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        return Response(TeamSerializer(team).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='move_playbook_to_team')
    def move_playbook_to_team(self, request, pk=None):
        """Add a playbook to team (admin only)."""
        logger.info(f'API: move_playbook_to_team team_id={pk} user={request.user.pk}')
        from methodology.services.team_service import TeamService
        from methodology.services.playbook_service import PlaybookService
        
        team = self.get_object()
        
        if team.admin_id != request.user.id:
            return Response(
                {"error": f"Only team admin can add playbooks to team {team.name}"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        playbook_id = request.data.get('playbook_id')
        if not playbook_id:
            return Response({"error": "playbook_id required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            playbook = PlaybookService.get_playbook(int(playbook_id), request.user)
            service = TeamService()
            service.add_playbook_to_team(team, playbook, request.user)
        except Playbook.DoesNotExist:
            return Response(
                {"error": f"Playbook {playbook_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "success": True,
            "team_id": team.id,
            "playbook_id": playbook.id,
            "playbook_name": playbook.name,
        })
    
    @action(detail=True, methods=['post'], url_path='move_playbook_from_team')
    def move_playbook_from_team(self, request, pk=None):
        """Remove a playbook from team (admin only)."""
        logger.info(f'API: move_playbook_from_team team_id={pk} user={request.user.pk}')
        from methodology.services.team_service import TeamService
        from methodology.services.playbook_service import PlaybookService
        
        team = self.get_object()
        
        if team.admin_id != request.user.id:
            return Response(
                {"error": f"Only team admin can remove playbooks from team {team.name}"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        playbook_id = request.data.get('playbook_id')
        if not playbook_id:
            return Response({"error": "playbook_id required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            playbook = PlaybookService.get_playbook(int(playbook_id), request.user)
            service = TeamService()
            service.remove_playbook_from_team(team, playbook, request.user)
        except Playbook.DoesNotExist:
            return Response(
                {"error": f"Playbook {playbook_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "success": True,
            "team_id": team.id,
            "playbook_id": playbook.id,
        })
    
    @action(detail=True, methods=['post'], url_path='invite')
    def invite(self, request, pk=None):
        """Invite users to join team (admin only)."""
        logger.info(f'API: invite_to_team team_id={pk} user={request.user.pk}')
        from methodology.services.team_invite_service import TeamInviteService
        
        team = self.get_object()
        
        if team.admin_id != request.user.id:
            return Response(
                {"error": f"Only team admin can invite users to team {team.name}"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        emails = request.data.get('emails', [])
        if not emails or not isinstance(emails, list):
            return Response({"error": "emails list required"}, status=status.HTTP_400_BAD_REQUEST)
        
        welcome_text = request.data.get('welcome_text', '')
        
        try:
            invite_service = TeamInviteService()
            results = invite_service.send_invites(team, request.user, emails, welcome_text)
        except ValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        invited_count = results.get("sent", 0) + results.get("created", 0)
        return Response({
            "success": True,
            "team_id": team.id,
            "invited_count": invited_count,
            "results": results,
        })
    
    @action(detail=True, methods=['post'], url_path='manage_invite')
    def manage_invite(self, request, pk=None):
        """Approve or reject a join request (admin only)."""
        logger.info(f'API: manage_team_invite team_id={pk} user={request.user.pk}')
        from methodology.services.team_service import TeamService
        
        team = self.get_object()
        
        if team.admin_id != request.user.id:
            return Response(
                {"error": f"Only team admin can manage join requests for team {team.name}"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        request_id = request.data.get('request_id')
        action_type = request.data.get('action')
        
        if not request_id or not action_type:
            return Response(
                {"error": "request_id and action required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if action_type not in ['approve', 'reject']:
            return Response(
                {"error": f"Invalid action: {action_type}. Must be 'approve' or 'reject'"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            join_request = JoinRequest.objects.select_related('user').get(pk=request_id, team=team)
        except JoinRequest.DoesNotExist:
            return Response(
                {"error": f"Join request {request_id} not found for team {pk}"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        try:
            service = TeamService()
            if action_type == 'approve':
                service.approve_join_request(join_request, request.user)
            else:
                service.reject_join_request(join_request, request.user)
        except ValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "success": True,
            "team_id": team.id,
            "request_id": request_id,
            "action": action_type,
            "user_email": join_request.user.email,
        })
