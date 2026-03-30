"""
Agent views for global list and search.

Provides a global list of all agents across playbooks owned by the user,
with search support via ?q= query parameter.
"""

import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

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
