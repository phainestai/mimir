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

from methodology.models import Playbook
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
    from methodology.models import Agent
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
    from methodology.models import Activity
    return (
        Activity.objects
        .filter(agent=agent)
        .select_related('workflow', 'workflow__playbook')
        .order_by('workflow__order', 'order')
    )
