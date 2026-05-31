"""
Content Browser views.

Provides the full-page graph explorer for playbooks at /browser/ and /browser/<pk>/.
Both views share a single template (browser/browser_graph.html) and differ only in
whether a playbook pk is passed to the template context.
"""

import logging

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from methodology.models import Playbook
from methodology.services.playbook_service import PlaybookService

logger = logging.getLogger(__name__)


def _playbook_readable_or_404(request, pk):
    """Return playbook if the logged-in user may view it; else Http404.

    Does not distinguish between "not found" and "not accessible" — both return 404
    to avoid revealing whether a private playbook exists.

    :param request: Django HTTP request.
    :param pk: int Playbook primary key.
    :returns: Playbook instance.
    :raises Http404: If playbook does not exist or is not accessible to request.user.

    Example return: Playbook(id=3, name="FeatureFactory", visibility="public", ...)
    """
    playbook = get_object_or_404(Playbook, pk=pk)
    if not playbook.can_view(request.user):
        logger.info(
            "User %s denied view on playbook id=%s (visibility=%s)",
            request.user.username,
            pk,
            playbook.visibility,
        )
        raise Http404()
    return playbook


@login_required
def browser_root(request):
    """Render the Content Browser with no playbook selected (empty canvas state).

    Route:    GET /browser/
    Template: browser/browser_graph.html
    Context:  playbook=None, playbook_pk=None

    The template renders the three-panel chrome with an empty-state canvas card.
    No graph data is fetched server-side; JS reads data-playbook-pk from the DOM.

    :param request: Django HTTP request.
    :returns: HttpResponse — 200 with three-panel shell, data-playbook-pk absent.
    """
    accessible = _get_accessible_playbooks(request.user)
    logger.info(
        "User %s accessed browser root (%s accessible playbooks)",
        request.user.username,
        len(accessible),
    )
    return render(
        request,
        "browser/browser_graph.html",
        {
            "playbook": None,
            "playbook_pk": None,
            "accessible_playbooks": accessible,
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
    playbook = _playbook_readable_or_404(request, pk)
    accessible = _get_accessible_playbooks(request.user)
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
            "accessible_playbooks": accessible,
        },
    )


def _get_accessible_playbooks(user):
    """Return list of playbooks accessible to user for the picker.

    Combines owned playbooks (any status), public non-draft playbooks, and
    team-shared playbooks. Delegates entirely to PlaybookService.

    :param user: Authenticated Django User instance.
    :returns: List of Playbook instances sorted by name, deduplicated.

    Example return: [Playbook(name="FeatureFactory"), Playbook(name="React Frontend"), ...]
    """
    owned = PlaybookService.list_playbooks(author=user)
    public = PlaybookService.list_public_playbooks(exclude_author=user)
    team = PlaybookService.list_team_playbooks_for_user(user)
    seen_ids = set()
    combined = []
    for pb in owned + public + team:
        if pb.pk not in seen_ids:
            seen_ids.add(pb.pk)
            combined.append(pb)
    combined.sort(key=lambda pb: pb.name.lower())
    return combined
