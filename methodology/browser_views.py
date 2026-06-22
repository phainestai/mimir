"""
Content Browser views.

Provides the full-page graph explorer for playbooks at /browser/ and /browser/<pk>/.
Both views share a single template (browser/browser_graph.html) and differ only in
whether a playbook pk is passed to the template context.
"""

import json
import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from methodology.services.phase_service import PhaseService
from methodology.utils.playbook_access import playbook_readable_or_404

logger = logging.getLogger(__name__)


@login_required
def browser_root(request):
    """Render the Content Browser with no playbook selected (empty canvas state).

    Route:    GET /browser/
    Template: browser/browser_graph.html
    Context:  playbook=None, playbook_pk=None

    The template renders the three-panel chrome with an empty-state canvas card.
    No graph data is fetched server-side; JS reads data-playbook-pk from the DOM.
    Playbook picker loads via GET /api/playbooks/ (client-side).

    :param request: Django HTTP request.
    :returns: HttpResponse — 200 with three-panel shell, data-playbook-pk absent.
    """
    logger.info("User %s accessed browser root", request.user.username)
    return render(
        request,
        "browser/browser_graph.html",
        {
            "playbook": None,
            "playbook_pk": None,
            "phases_json": "[]",
        },
    )


@login_required
def browser_playbook(request, pk):
    """Render the Content Browser pre-loaded for a specific playbook.

    Route:    GET /browser/<pk>/
    Template: browser/browser_graph.html
    Context:  playbook=<Playbook>, playbook_pk=pk

    The template passes pk as data-playbook-pk so content-browser.js can fetch
    the graph on init. All graph rendering happens client-side.

    :param request: Django HTTP request.
    :param pk: int Playbook primary key.
    :returns: HttpResponse — 200 with three-panel shell and data-playbook-pk="{{ pk }}".
    :raises Http404: If playbook not found or not accessible to request.user.

    Example: GET /browser/3/ → 200, context includes playbook=FeatureFactory
    """
    playbook = playbook_readable_or_404(request, pk)
    phases = PhaseService.list_phases(pk, request.user)
    phases_json = json.dumps([{"id": p.id, "name": p.name} for p in phases])
    logger.info(
        "User %s accessed browser for playbook id=%s name=%s",
        request.user.username,
        pk,
        playbook.name,
    )
    return render(
        request,
        "browser/browser_graph.html",
        {
            "playbook": playbook,
            "playbook_pk": pk,
            "phases_json": phases_json,
        },
    )
