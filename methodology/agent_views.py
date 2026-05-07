"""
Agent views for global list, create, and detail operations.

Provides a global list of all agents across playbooks owned by the user,
with search support via ?q= query parameter, plus playbook-scoped create
and per-agent detail views.
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from methodology.models import Activity, Agent, Playbook
from methodology.services.agent_service import AgentService

logger = logging.getLogger(__name__)


@login_required
def agent_list_global(request):
    """
    Global agents list — all agents across all playbooks owned by the user.

    Supports search via ?q= query parameter (matches name and description).

    Template: agents/list.html
    Template Context:
        - agents: QuerySet of Agent instances (filtered by query if provided)
        - query: Current search string
        - total_count: Total agents before filtering

    :param request: Django request object
    :return: Rendered global list template
    """
    query = request.GET.get('q', '').strip()
    agents = AgentService.search_agents(query=query, user=request.user)
    total_count = AgentService.search_agents(query='', user=request.user).count()

    logger.info(
        f"User {request.user.username} viewing global agent list"
        + (f", query={query!r}" if query else "")
    )

    context = {
        'agents': agents,
        'query': query,
        'total_count': total_count,
    }
    return render(request, 'agents/list.html', context)


@login_required
def agent_list_for_playbook(request, playbook_pk):
    playbook = get_object_or_404(Playbook, pk=playbook_pk, author=request.user)
    agents = AgentService.list_agents_for_playbook(playbook_pk)
    cnt = agents.count()
    logger.info(
        'User %s viewing agents for playbook %s (count=%d)',
        request.user.username,
        playbook_pk,
        cnt,
    )
    return render(request, 'agents/playbook_list.html', {
        'playbook': playbook,
        'agents': agents,
        'can_edit': playbook.can_edit(request.user),
    })


# ==================== CREATE ====================


@login_required
def agent_create(request, playbook_pk):
    """
    Create a new agent for a playbook.

    GET: Display create form.
    POST: Validate and create agent, redirect to playbook detail on success.

    Template: agents/create.html
    Template Context:
        - playbook: Playbook instance
        - form_data: Dict with submitted field values (on validation error)
        - errors: Dict with field-level error messages (on validation error)

    :param request: Django request object
    :param playbook_pk: Playbook primary key
    :return: Rendered form template or redirect
    :raises Http404: If playbook not found
    """
    playbook = get_object_or_404(Playbook, pk=playbook_pk)

    if not playbook.is_owned_by(request.user):
        logger.warning(
            f"User {request.user.username} attempted to create agent without permission"
        )
        messages.error(request, "You don't have permission to add agents to this playbook.")
        return redirect('playbook_detail', pk=playbook_pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        errors = _validate_agent_form(name)
        if not errors:
            try:
                agent = AgentService.create_agent(
                    playbook=playbook,
                    name=name,
                    description=description,
                )
                logger.info(
                    f"User {request.user.username} created agent '{name}' "
                    f"in playbook {playbook_pk}"
                )
                messages.success(request, f"Agent '{agent.name}' created successfully!")
                return redirect('agent_detail', pk=agent.pk)
            except ValidationError as e:
                logger.warning(f"Agent creation validation error: {e}")
                errors['name'] = str(e.message)

        return _render_create_form(request, playbook, request.POST, errors)

    logger.info(
        f"User {request.user.username} opening agent create form for playbook {playbook_pk}"
    )
    return _render_create_form(request, playbook, {}, {})


def _validate_agent_form(name):
    """
    Validate agent form fields and return dict of field-level errors.

    :param name: Agent name string from form submission
    :returns: Dict mapping field name to error message (empty if valid)
    :rtype: dict
    """
    errors = {}
    if not name:
        errors['name'] = 'This field is required.'
    elif len(name) > 200:
        errors['name'] = 'Agent name cannot exceed 200 characters'
    return errors


def _render_create_form(request, playbook, form_data, errors):
    """Render agent create form with context."""
    context = {
        'playbook': playbook,
        'form_data': form_data,
        'errors': errors,
    }
    return render(request, 'agents/create.html', context)


# ==================== DETAIL ====================


@login_required
def agent_detail(request, pk):
    """
    Display agent details including associated activities.

    Template: agents/detail.html
    Template Context:
        - agent: Agent instance
        - playbook: Playbook instance
        - activities: QuerySet of Activity instances assigned to this agent
        - can_edit: Boolean indicating if user can edit

    :param request: Django request object
    :param pk: Agent primary key
    :return: Rendered detail template
    :raises Http404: If agent not found
    """
    agent = get_object_or_404(
        Agent.objects.select_related('playbook', 'playbook__author'),
        pk=pk,
    )

    if not agent.is_owned_by(request.user):
        logger.warning(
            f"User {request.user.username} attempted to view agent {pk} they don't own"
        )
        messages.error(request, "You don't have permission to view this agent.")
        return redirect('agent_list')

    activities = _get_activities_for_agent(agent)

    logger.info(f"User {request.user.username} viewing agent {pk}")
    context = {
        'agent': agent,
        'playbook': agent.playbook,
        'activities': activities,
        'can_edit': agent.can_edit(request.user),
    }
    return render(request, 'agents/detail.html', context)


def _get_activities_for_agent(agent):
    """
    Return activities assigned to this agent, ordered by workflow then activity order.

    :param agent: Agent instance
    :returns: QuerySet of Activity instances
    :rtype: QuerySet
    """
    return (
        Activity.objects
        .filter(agent=agent)
        .select_related('workflow', 'workflow__playbook')
        .order_by('workflow__order', 'order')
    )


# ==================== EDIT ====================


@login_required
def agent_edit(request, pk):
    """
    Edit existing agent.

    GET: Display edit form with pre-populated data.
    POST: Validate and update agent, redirect to detail view on success.

    Template: agents/edit.html
    Template Context:
        - agent: Agent instance being edited
        - form_data: Dict with current field values (GET) or user input (POST on error)
        - errors: Dict with field-level error messages (empty on GET, populated on POST error)
        - playbook: Playbook instance for breadcrumbs

    :param request: Django request object
    :param pk: Agent primary key
    :return: Rendered edit form template or redirect
    :raises Http404: If agent not found
    """
    agent = get_object_or_404(
        Agent.objects.select_related('playbook', 'playbook__author'),
        pk=pk,
    )

    if not agent.can_edit(request.user):
        logger.warning(
            f"User {request.user.username} attempted to edit agent {pk} without permission"
        )
        messages.error(request, "You don't have permission to edit this agent.")
        return redirect('agent_detail', pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        form_data = {'name': name, 'description': description}

        try:
            updated_agent = AgentService.update_agent(pk, name=name, description=description)
            logger.info(
                f"User {request.user.username} updated agent {pk} '{updated_agent.name}'"
            )
            messages.success(request, f'Agent "{updated_agent.name}" updated successfully.')
            return redirect('agent_detail', pk=pk)
        except ValidationError as e:
            errors = _extract_validation_errors(e)
            return _render_edit_form(request, agent, form_data, errors)

    form_data = {'name': agent.name, 'description': agent.description}
    logger.info(f"User {request.user.username} opening agent edit form for agent {pk}")
    return _render_edit_form(request, agent, form_data, {})


def _extract_validation_errors(exc):
    """
    Extract field-level errors from a ValidationError into a flat dict.

    :param exc: ValidationError raised by AgentService
    :returns: Dict mapping field name to first error message string
    :rtype: dict

    Example:
        >>> # exc.message_dict = {'name': ['Agent already exists']}
        >>> _extract_validation_errors(exc)
        {'name': 'Agent already exists'}
        >>> # exc with plain message: "Agent name cannot be empty"
        >>> _extract_validation_errors(exc)
        {'name': 'Agent name cannot be empty'}
    """
    if hasattr(exc, 'message_dict'):
        return {field: msgs[0] if isinstance(msgs, list) else msgs
                for field, msgs in exc.message_dict.items()}
    if hasattr(exc, 'messages') and exc.messages:
        return {'name': exc.messages[0]}
    return {'name': str(exc)}


def _render_edit_form(request, agent, form_data, errors):
    """
    Render agent edit form with context.

    :param request: Django request object
    :param agent: Agent instance being edited
    :param form_data: Dict with current or user-submitted field values
    :param errors: Dict mapping field names to error message strings
    :returns: Rendered agents/edit.html response
    :rtype: HttpResponse

    Example:
        >>> return _render_edit_form(request, agent, {'name': 'Reviewer'}, {'name': 'Required'})
    """
    context = {
        'agent': agent,
        'form_data': form_data,
        'errors': errors,
        'playbook': agent.playbook,
    }
    return render(request, 'agents/edit.html', context)


# ==================== DELETE ====================


@login_required
def agent_delete(request, pk):
    """
    Delete agent with HTMX confirmation modal.

    GET: Render delete confirmation modal partial with cascade warnings.
    POST: Delete agent (activities retain NULL agent), redirect to playbook detail.

    Template: agents/_delete_modal.html (GET only)
    Template Context:
        - agent: Agent instance to delete
        - activity_count: int total activities using this agent
        - activities: QuerySet of first 5 activities (for display)

    :param request: Django request object
    :param pk: Agent primary key
    :return: Rendered modal partial (GET) or redirect (POST)
    :raises Http404: If agent not found
    """
    agent = get_object_or_404(
        Agent.objects.select_related('playbook', 'playbook__author'),
        pk=pk,
    )

    if not agent.can_edit(request.user):
        logger.warning(
            f"User {request.user.username} attempted to delete agent {pk} without permission"
        )
        messages.error(request, "You don't have permission to delete this agent.")
        return redirect('agent_detail', pk=pk)

    if request.method == 'POST':
        playbook_id = agent.playbook_id
        agent_name = agent.name
        AgentService.delete_agent(pk)
        logger.info(
            f"User {request.user.username} deleted agent '{agent_name}' (id={pk})"
        )
        messages.success(request, f'Agent "{agent_name}" deleted successfully.')
        return redirect('playbook_detail', pk=playbook_id)

    activities = agent.activities.select_related('workflow').order_by('name')[:5]
    activity_count = agent.get_activity_count()
    logger.info(
        f"User {request.user.username} opening delete modal for agent {pk}"
    )
    context = {
        'agent': agent,
        'activity_count': activity_count,
        'activities': activities,
    }
    return render(request, 'agents/_delete_modal.html', context)
