"""
Activity views for CRUDV operations.

Provides views for listing, creating, viewing, editing, and deleting activities
within workflows.
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError

from methodology.models import Playbook, Workflow, Activity, ArtifactInput, Rule
from methodology.services.activity_service import ActivityService

logger = logging.getLogger(__name__)


# ==================== GLOBAL LIST ====================

@login_required
def activity_global_list(request):
    """
    Global activities overview - all activities across all workflows and playbooks.
    
    Shows activities from all workflows in playbooks owned by the user.
    Useful for seeing all tasks and managing across entire methodology.
    
    Template: activities/global_list.html
    Template Context:
        - activities: QuerySet of all activities
        - workflow_count: Count of unique workflows
        - playbook_count: Count of unique playbooks
        - phase_groups: Dict of activities grouped by phase
    
    :param request: Django request object
    :return: Rendered global list template
    """
    # Get all activities from user's owned playbooks
    activities = Activity.objects.filter(
        workflow__playbook__author=request.user,
        workflow__playbook__source='owned'
    ).select_related('workflow', 'workflow__playbook').order_by(
        'workflow__playbook__name', 'workflow__order', 'order'
    )
    
    # Count unique workflows and playbooks
    workflow_count = activities.values('workflow').distinct().count()
    playbook_count = activities.values('workflow__playbook').distinct().count()
    
    # Group by phase for overview
    phase_groups = {}
    for activity in activities:
        phase_name = activity.phase.name if activity.phase else 'Unassigned'
        if phase_name not in phase_groups:
            phase_groups[phase_name] = []
        phase_groups[phase_name].append(activity)
    
    logger.info(f"User {request.user.username} viewing global activities list ({activities.count()} activities)")
    
    return render(request, 'activities/global_list.html', {
        'activities': activities,
        'workflow_count': workflow_count,
        'playbook_count': playbook_count,
        'phase_groups': phase_groups,
    })


@login_required
def activity_list_for_playbook(request, playbook_pk):
    playbook = get_object_or_404(Playbook, pk=playbook_pk, author=request.user)
    activities_qs = ActivityService.list_activities_for_playbook(playbook_pk, request.user)
    cnt = activities_qs.count()
    logger.info(
        'User %s viewing activities for playbook %s (count=%d)',
        request.user.username,
        playbook_pk,
        cnt,
    )
    return render(request, 'activities/playbook_list.html', {
        'playbook': playbook,
        'activities': activities_qs,
        'can_edit': playbook.can_edit(request.user),
    })


# ==================== LIST ====================

@login_required
def activity_list(request, playbook_pk, workflow_pk):
    """
    List all activities in a workflow.
    
    Displays activities grouped by phase if phases exist, otherwise shows
    flat list ordered by sequence. Includes permission checks and activity
    count statistics.
    
    Template: activities/list.html
    Template Context:
        - playbook: Playbook instance
        - workflow: Workflow instance
        - activities_by_phase: Dict of phase -> activities list
        - has_phases: Boolean indicating if any activities have phases
        - total_activities: Count of all activities
        - can_edit: Boolean indicating if user can create/edit activities
    
    :param request: Django request object
    :param playbook_pk: Playbook primary key
    :param workflow_pk: Workflow primary key
    :return: Rendered list template
    :raises Http404: If playbook or workflow not found
    """
    logger.info(f"User {request.user.username} accessing activity list for workflow {workflow_pk}")
    
    # Get workflow and playbook with permission check
    playbook = get_object_or_404(Playbook, pk=playbook_pk)
    workflow = get_object_or_404(Workflow, pk=workflow_pk, playbook=playbook)
    
    # Check if user has access to this playbook
    if playbook.source == 'owned' and playbook.author != request.user:
        logger.warning(f"User {request.user.username} attempted to access workflow {workflow_pk} they don't own")
        messages.error(request, "You don't have permission to view this workflow's activities.")
        return redirect('playbook_list')
    
    # Get activities grouped by phase
    activities_by_phase = ActivityService.get_activities_grouped_by_phase(workflow)
    total_activities = sum(len(acts) for acts in activities_by_phase.values())
    
    # Check if workflow has phases (more than just "Unassigned")
    has_phases = len(activities_by_phase) > 1 or (
        len(activities_by_phase) == 1 and 'Unassigned' not in activities_by_phase
    )
    
    logger.info(f"Loaded {total_activities} activities with {len(activities_by_phase)} phases for workflow {workflow_pk}")
    
    context = {
        'playbook': playbook,
        'workflow': workflow,
        'activities_by_phase': activities_by_phase,
        'has_phases': has_phases,
        'total_activities': total_activities,
        'can_edit': workflow.can_edit(request.user),
    }
    
    return render(request, 'activities/list.html', context)


# ==================== CREATE ====================

@login_required
def activity_create(request, playbook_pk, workflow_pk):
    """
    Create new activity in workflow.
    
    GET: Display create form
    POST: Validate and create activity, redirect to list
    
    Template: activities/create.html
    Template Context:
        - playbook: Playbook instance
        - workflow: Workflow instance
        - form_data: Dict with form values (on validation error)
        - errors: Dict with field errors (on validation error)
    
    :param request: Django request object
    :param playbook_pk: Playbook primary key
    :param workflow_pk: Workflow primary key
    :return: Rendered form template or redirect
    :raises Http404: If playbook or workflow not found
    """
    logger.info(f"User {request.user.username} accessing activity create for workflow {workflow_pk}")
    
    # Get workflow and playbook with permission check
    playbook = get_object_or_404(Playbook, pk=playbook_pk)
    workflow = get_object_or_404(Workflow, pk=workflow_pk, playbook=playbook)
    
    # Check edit permission
    if not workflow.can_edit(request.user):
        logger.warning(f"User {request.user.username} attempted to create activity without permission")
        messages.error(request, "You don't have permission to add activities to this workflow.")
        return redirect('activity_list', playbook_pk=playbook_pk, workflow_pk=workflow_pk)
    
    if request.method == 'POST':
        # Extract form data
        name = request.POST.get('name', '').strip()
        guidance = request.POST.get('guidance', '').strip()
        phase = request.POST.get('phase', '').strip() or None
        order = request.POST.get('order', '').strip()
        predecessor_id = request.POST.get('predecessor', '').strip() or None
        successor_id = request.POST.get('successor', '').strip() or None
        
        # Convert order to int if provided
        order_int = None
        if order:
            try:
                order_int = int(order)
            except ValueError:
                messages.error(request, 'Order must be a number.')
                return _render_create_form(request, playbook, workflow, request.POST, {'order': 'Must be a number'})
        
        # Get predecessor and successor objects if IDs provided
        predecessor = None
        successor = None
        if predecessor_id:
            try:
                predecessor = Activity.objects.get(pk=int(predecessor_id), workflow=workflow)
            except (Activity.DoesNotExist, ValueError):
                messages.error(request, 'Invalid predecessor selected.')
                return _render_create_form(request, playbook, workflow, request.POST, {})
        
        if successor_id:
            try:
                successor = Activity.objects.get(pk=int(successor_id), workflow=workflow)
            except (Activity.DoesNotExist, ValueError):
                messages.error(request, 'Invalid successor selected.')
                return _render_create_form(request, playbook, workflow, request.POST, {})
        
        # Validate and create
        try:
            # Convert phase to phase_id (int or None)
            phase_id = int(phase) if phase else None
            
            activity = ActivityService.create_activity(
                workflow=workflow,
                name=name,
                guidance=guidance,
                phase_id=phase_id,
                order=order_int,
                predecessor=predecessor,
                successor=successor
            )
            rule_ids = request.POST.getlist('rules')
            ActivityService.set_activity_rules(activity.pk, rule_ids)
            logger.info(f"Activity '{name}' created successfully in workflow {workflow_pk}")
            messages.success(request, f"Activity '{activity.name}' created successfully!")
            return redirect('activity_list', playbook_pk=playbook_pk, workflow_pk=workflow_pk)
            
        except ValidationError as e:
            logger.warning(f"Activity creation validation error: {str(e)}")
            messages.error(request, str(e))
            return _render_create_form(request, playbook, workflow, request.POST, {})
    
    # GET request - show form
    return _render_create_form(request, playbook, workflow, {}, {})


def _render_create_form(request, playbook, workflow, form_data, errors):
    """Helper to render create form with context."""
    from methodology.models import Phase

    # Get available predecessors and successors
    available_predecessors = ActivityService.get_available_predecessors(workflow)
    available_successors = ActivityService.get_available_successors(workflow)

    # Get available phases for this playbook
    available_phases = Phase.objects.filter(playbook=playbook).order_by('order')
    available_rules = Rule.objects.filter(playbook=playbook).order_by('title')
    
    # Check if dropdowns should be disabled (no other activities)
    disable_dependencies = workflow.get_activity_count() == 0

    if hasattr(form_data, 'getlist'):
        selected_rule_ids = [str(x) for x in form_data.getlist('rules')]
    else:
        selected_rule_ids = [str(x) for x in (form_data.get('rules') or [])]

    context = {
        'playbook': playbook,
        'workflow': workflow,
        'form_data': form_data,
        'errors': errors,
        'available_predecessors': available_predecessors,
        'available_successors': available_successors,
        'available_phases': available_phases,
        'available_rules': available_rules,
        'selected_rule_ids': selected_rule_ids,
        'disable_dependencies': disable_dependencies,
    }
    return render(request, 'activities/create.html', context)


# ==================== VIEW ====================

@login_required
def activity_detail(request, playbook_pk, workflow_pk, activity_pk):
    """
    View activity details.
    
    Displays full activity information including name, guidance (rich Markdown), phase,
    dependencies, order, and timestamps.
    
    Template: activities/detail.html
    Template Context:
        - playbook: Playbook instance
        - workflow: Workflow instance
        - activity: Activity instance
        - can_edit: Boolean indicating if user can edit
    
    :param request: Django request object
    :param playbook_pk: Playbook primary key
    :param workflow_pk: Workflow primary key
    :param activity_pk: Activity primary key
    :return: Rendered detail template
    :raises Http404: If playbook, workflow, or activity not found
    """
    logger.info(f"User {request.user.username} viewing activity {activity_pk}")
    
    # Get instances with permission check
    playbook = get_object_or_404(Playbook, pk=playbook_pk)
    workflow = get_object_or_404(Workflow, pk=workflow_pk, playbook=playbook)
    activity = get_object_or_404(
        Activity.objects.select_related('predecessor', 'successor').prefetch_related('rules'),
        pk=activity_pk,
        workflow=workflow
    )
    
    # Check if user has access
    if playbook.source == 'owned' and playbook.author != request.user:
        logger.warning(f"User {request.user.username} attempted to access activity {activity_pk} they don't own")
        messages.error(request, "You don't have permission to view this activity.")
        return redirect('playbook_list')
    
    
    # Get artifact inputs for this activity
    artifact_inputs = ArtifactInput.objects.filter(
        activity=activity
    ).select_related('artifact', 'artifact__produced_by').order_by('artifact__name')
    logger.info(f"Activity {activity_pk} has {artifact_inputs.count()} artifact inputs")

    context = {
        'playbook': playbook,
        'workflow': workflow,
        'activity': activity,
        'can_edit': workflow.can_edit(request.user),
        'artifact_inputs': artifact_inputs,

    }
    
    logger.info(f"Activity detail rendered for user {request.user.username}")
    return render(request, 'activities/detail.html', context)


# ==================== EDIT ====================

@login_required
def activity_edit(request, playbook_pk, workflow_pk, activity_pk):
    """
    Edit activity.
    
    GET: Display edit form with current values
    POST: Validate and update activity, redirect to detail
    
    Template: activities/edit.html
    Template Context:
        - playbook: Playbook instance
        - workflow: Workflow instance
        - activity: Activity instance
        - form_data: Dict with form values (on validation error)
        - errors: Dict with field errors (on validation error)
    
    :param request: Django request object
    :param playbook_pk: Playbook primary key
    :param workflow_pk: Workflow primary key
    :param activity_pk: Activity primary key
    :return: Rendered form template or redirect
    :raises Http404: If playbook, workflow, or activity not found
    """
    logger.info(f"User {request.user.username} editing activity {activity_pk}")
    
    # Get instances with permission check
    playbook = get_object_or_404(Playbook, pk=playbook_pk)
    workflow = get_object_or_404(Workflow, pk=workflow_pk, playbook=playbook)
    activity = get_object_or_404(
        Activity.objects.select_related('predecessor', 'successor').prefetch_related('rules'),
        pk=activity_pk,
        workflow=workflow
    )
    
    # Check edit permission
    if not activity.can_edit(request.user):
        messages.error(request, "You don't have permission to edit this activity.")
        return redirect('activity_detail', playbook_pk=playbook_pk, workflow_pk=workflow_pk, activity_pk=activity_pk)
    
    if request.method == 'POST':
        # Extract form data
        name = request.POST.get('name', '').strip()
        guidance = request.POST.get('guidance', '').strip()
        phase = request.POST.get('phase', '').strip() or None
        order = request.POST.get('order', '').strip()
        predecessor_id = request.POST.get('predecessor', '').strip() or None
        successor_id = request.POST.get('successor', '').strip() or None
        agent_id = request.POST.get('agent', '').strip() or None
        skill_id = request.POST.get('skill', '').strip() or None
        artifact_input_ids = request.POST.getlist('artifact_inputs')
        rule_ids = request.POST.getlist('rules')

        # Convert order to int
        order_int = None
        if order:
            try:
                order_int = int(order)
            except ValueError:
                messages.error(request, 'Order must be a number.')
                return _render_edit_form(request, playbook, workflow, activity, request.POST, {'order': 'Must be a number'})
        
        # Get predecessor and successor objects if IDs provided
        predecessor = None
        successor = None
        if predecessor_id:
            try:
                pred_id = int(predecessor_id)
                if pred_id != activity_pk:  # Don't allow self-reference
                    predecessor = Activity.objects.get(pk=pred_id, workflow=workflow)
            except (Activity.DoesNotExist, ValueError):
                messages.error(request, 'Invalid predecessor selected.')
                return _render_edit_form(request, playbook, workflow, activity, request.POST, {})
        
        if successor_id:
            try:
                succ_id = int(successor_id)
                if succ_id != activity_pk:  # Don't allow self-reference
                    successor = Activity.objects.get(pk=succ_id, workflow=workflow)
            except (Activity.DoesNotExist, ValueError):
                messages.error(request, 'Invalid successor selected.')
                return _render_edit_form(request, playbook, workflow, activity, request.POST, {})
        
        # Validate and update
        try:
            # Convert phase to phase_id (int or None)
            phase_id = int(phase) if phase else None
            
            update_fields = {
                'name': name,
                'guidance': guidance,
                'phase_id': phase_id,
                'predecessor': predecessor,
                'successor': successor,
            }
            if order_int is not None:
                update_fields['order'] = order_int
            
            ActivityService.update_activity(activity_pk, **update_fields)
            
            # Handle agent linking
            if agent_id:
                ActivityService.set_activity_agent(activity_pk, int(agent_id))
                logger.info(f"Agent {agent_id} linked to activity {activity_pk}")
            else:
                ActivityService.clear_activity_agent(activity_pk)
                logger.info(f"Agent unlinked from activity {activity_pk}")
            
            # Handle skill linking
            if skill_id:
                ActivityService.set_activity_skill(activity_pk, int(skill_id))
                logger.info(f"Skill {skill_id} linked to activity {activity_pk}")
            else:
                ActivityService.clear_activity_skill(activity_pk)
                logger.info(f"Skill unlinked from activity {activity_pk}")
            
            # Handle artifact inputs
            artifact_ids_int = [int(aid) for aid in artifact_input_ids if aid]
            ActivityService.set_activity_artifact_inputs(activity_pk, artifact_ids_int)
            ActivityService.set_activity_rules(activity_pk, rule_ids)

            logger.info(f"Activity {activity_pk} updated successfully with {len(artifact_ids_int)} artifact inputs")
            logger.info(f"Activity {activity_pk} updated successfully")
            messages.success(request, f"Activity '{name}' updated successfully!")
            return redirect('activity_detail', playbook_pk=playbook_pk, workflow_pk=workflow_pk, activity_pk=activity_pk)
            
        except ValidationError as e:
            logger.warning(f"Activity edit validation error: {str(e)}")
            messages.error(request, str(e))
            return _render_edit_form(request, playbook, workflow, activity, request.POST, {})
    
    # GET request - show form with current values
    form_data = {
        'name': activity.name,
        'guidance': activity.guidance,
        'phase': activity.phase.id if activity.phase else '',
        'order': activity.order,
        'predecessor': activity.predecessor.id if activity.predecessor else '',
        'successor': activity.successor.id if activity.successor else '',
        'agent': activity.agent.id if activity.agent else '',
        'skill': activity.skill.id if activity.skill else '',
        'artifact_inputs': list(ArtifactInput.objects.filter(activity=activity).values_list('artifact_id', flat=True)),
        'rules': list(activity.rules.values_list('id', flat=True)),

    }
    return _render_edit_form(request, playbook, workflow, activity, form_data, {})


def _render_edit_form(request, playbook, workflow, activity, form_data, errors):
    """Helper to render edit form with context."""
    # Get available predecessors and successors (exclude current activity)
    available_predecessors = ActivityService.get_available_predecessors(workflow, exclude_activity_id=activity.id)

    # Get available agents, skills, artifacts, and phases from playbook
    from methodology.models import Agent, Skill, Artifact, Phase
    available_agents = Agent.objects.filter(playbook=playbook).order_by('name')
    available_skills = Skill.objects.filter(playbook=playbook).order_by('title')
    available_phases = Phase.objects.filter(playbook=playbook).order_by('order')
    
    # Exclude artifacts produced by this activity
    available_artifacts = Artifact.objects.filter(
        playbook=playbook
    ).exclude(
        produced_by=activity
    ).select_related('produced_by').order_by('produced_by__name', 'name')

    available_successors = ActivityService.get_available_successors(workflow, exclude_activity_id=activity.id)

    available_rules = Rule.objects.filter(playbook=playbook).order_by('title')

    # Check if dropdowns should be disabled (only 1 activity - the current one)
    disable_dependencies = workflow.get_activity_count() <= 1

    context = {
        'playbook': playbook,
        'workflow': workflow,
        'activity': activity,
        'form_data': form_data,
        'available_agents': available_agents,
        'available_skills': available_skills,
        'available_rules': available_rules,
        'available_artifacts': available_artifacts,
        'available_phases': available_phases,

        'errors': errors,
        'available_predecessors': available_predecessors,
        'available_successors': available_successors,
        'disable_dependencies': disable_dependencies,
    }
    return render(request, 'activities/edit.html', context)


# ==================== DELETE ====================

@login_required
def activity_delete(request, playbook_pk, workflow_pk, activity_pk):
    """
    Delete activity.
    
    GET: Show confirmation page
    POST: Delete activity and redirect to list
    
    Template: activities/delete.html (confirmation)
    Template Context:
        - playbook: Playbook instance
        - workflow: Workflow instance
        - activity: Activity instance
    
    :param request: Django request object
    :param playbook_pk: Playbook primary key
    :param workflow_pk: Workflow primary key
    :param activity_pk: Activity primary key
    :return: Rendered confirmation template or redirect
    :raises Http404: If playbook, workflow, or activity not found
    """
    logger.info(f"User {request.user.username} deleting activity {activity_pk}")
    
    # Get instances with permission check
    playbook = get_object_or_404(Playbook, pk=playbook_pk)
    workflow = get_object_or_404(Workflow, pk=workflow_pk, playbook=playbook)
    activity = get_object_or_404(Activity, pk=activity_pk, workflow=workflow)
    
    # Check edit permission
    if not workflow.can_edit(request.user):
        logger.warning(f"User {request.user.username} attempted to delete activity without permission")
        messages.error(request, "You don't have permission to delete this activity.")
        return redirect('activity_detail', playbook_pk=playbook_pk, workflow_pk=workflow_pk, activity_pk=activity_pk)
    
    if request.method == 'POST':
        # Confirm deletion
        activity_name = activity.name
        try:
            ActivityService.delete_activity(activity_pk)
            logger.info(f"Activity '{activity_name}' deleted successfully")
            messages.success(request, f"Activity '{activity_name}' deleted successfully!")
            return redirect('activity_list', playbook_pk=playbook_pk, workflow_pk=workflow_pk)
        except Exception as e:
            logger.error(f"Error deleting activity {activity_pk}: {str(e)}")
            messages.error(request, f"Failed to delete activity: {str(e)}")
            return redirect('activity_detail', playbook_pk=playbook_pk, workflow_pk=workflow_pk, activity_pk=activity_pk)
    
    # GET request - show confirmation
    context = {
        'playbook': playbook,
        'workflow': workflow,
        'activity': activity,
    }
    return render(request, 'activities/delete.html', context)
