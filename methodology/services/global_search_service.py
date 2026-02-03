"""Service for NAV-06 Global search across playbooks, workflows, and activities."""

import logging
from typing import Any, Dict, List, Optional

from django.db.models import Q, QuerySet

from methodology.models import Activity, Playbook, Workflow

logger = logging.getLogger(__name__)


class GlobalSearchService:
    """Service responsible for global search behavior.

    Provides a single entry point for searching across multiple entity types
    while applying basic access rules.
    """

    def search(self, query: str, user, filters: Optional[Dict[str, Any]] = None) -> Dict[str, List[Any]]:
        """Search across playbooks, workflows, and activities.

        :param query: Free-text query, e.g. "Component".
        :param user: Django user performing the search. Example: User(username="maria").
        :param filters: Optional dict of filters (reserved for future use).
        :return: Dict with lists of playbooks, workflows, activities.
                 Example:
                 {
                     "playbooks": [Playbook(...), ...],
                     "workflows": [Workflow(...), ...],
                     "activities": [Activity(...), ...],
                 }
        :raises: None. Returns empty lists when query is empty.
        """
        filters = filters or {}
        normalized_query = (query or "").strip()

        if not normalized_query:
            logger.info("GlobalSearchService.search called with empty query by user=%s", user.username)
            return {"playbooks": [], "workflows": [], "activities": []}

        logger.info(
            "GlobalSearchService.search started for user=%s, query='%s', filters=%s",
            user.username,
            normalized_query,
            filters,
        )

        playbooks_qs = self._search_playbooks(normalized_query, user, filters)
        workflows_qs = self._search_workflows(normalized_query, user, filters)
        activities_qs = self._search_activities(normalized_query, user, filters)

        playbooks = list(playbooks_qs)
        workflows = list(workflows_qs)
        activities = list(activities_qs)

        # Apply type-level filtering at the aggregation layer
        type_filter = filters.get("type")
        if type_filter == "playbooks":
            workflows = []
            activities = []
        elif type_filter == "workflows":
            playbooks = []
            activities = []
        elif type_filter == "activities":
            playbooks = []
            workflows = []

        logger.info(
            "GlobalSearchService.search finished for user=%s, query='%s' with %d playbooks, %d workflows, %d activities",
            user.username,
            normalized_query,
            len(playbooks),
            len(workflows),
            len(activities),
        )

        return {
            "playbooks": playbooks,
            "workflows": workflows,
            "activities": activities,
        }

    def _search_playbooks(self, query: str, user, filters: Dict[str, Any]) -> QuerySet[Playbook]:
        """Search playbooks owned by the user, matching name or description.

        Respects optional filters:
        - status: playbook status value
        - source: playbook source value
        """
        base_qs = Playbook.objects.filter(author=user)

        status = filters.get("status")
        if status:
            base_qs = base_qs.filter(status=status)

        source = filters.get("source")
        if source:
            base_qs = base_qs.filter(source=source)

        return base_qs.filter(Q(name__icontains=query) | Q(description__icontains=query)).order_by("-updated_at")

    def _search_workflows(self, query: str, user, filters: Dict[str, Any]) -> QuerySet[Workflow]:
        """Search workflows within the user's playbooks."""
        base_qs = Workflow.objects.filter(playbook__author=user)
        return base_qs.filter(Q(name__icontains=query) | Q(description__icontains=query)).order_by("playbook", "order")

    def _search_activities(self, query: str, user, filters: Dict[str, Any]) -> QuerySet[Activity]:
        """Search activities within workflows of the user's playbooks."""
        base_qs = Activity.objects.filter(workflow__playbook__author=user)
        return base_qs.filter(Q(name__icontains=query) | Q(guidance__icontains=query)).order_by("workflow", "order")
