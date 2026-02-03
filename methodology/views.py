"""Views for the methodology app."""
import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from methodology.services.global_search_service import GlobalSearchService
logger = logging.getLogger(__name__)


def index(request):
    """
    Home page - methodology explorer landing page. Public access allowed.
    
    :param request: Django request object. Example: HttpRequest(method='GET', user=<User: admin>)
    :return: Rendered HTML response. Example: HttpResponse(status=200, content="<div>...</div>")
    """
    return render(request, 'methodology/index.html')


@login_required
def dashboard(request):
    """
    Dashboard view with activity feed and recent playbooks (FOB-DASHBOARD-1).
    
    Displays user's personalized dashboard with:
    - My Playbooks section (5 most recent playbooks)
    - Recent Activity feed (10 most recent actions)
    - Quick Actions panel
    
    Template: dashboard.html
    Context:
        recent_playbooks: List of recent Playbook objects
        recent_activities: QuerySet of recent Activity objects
        activity_count: Number of recent activities
        playbook_count: Number of recent playbooks
    
    :param request: Django request object. Example: HttpRequest(method='GET', user=<User: maria>)
    :return: Rendered HTML response with dashboard data. Example: HttpResponse(status=200, content="<div>...</div>")
    :raises: None - handles all exceptions gracefully
    """
    logger.info(f"User {request.user.username} accessing dashboard")
    
    try:
        from methodology.services.activity_service import ActivityService
        from methodology.services.playbook_service import PlaybookService
        from methodology.models import Playbook, Activity
        
        # Get recent playbooks (last 5 updated)
        recent_playbooks = Playbook.objects.filter(
            author=request.user
        ).order_by('-updated_at')[:5]
        
        # Get recent activities (last 10 updated)
        recent_activities = ActivityService.get_recent_activities(request.user, limit=10)
        
        # Get counts
        playbook_count = Playbook.objects.filter(author=request.user).count()
        activity_count = Activity.objects.filter(
            workflow__playbook__author=request.user
        ).count()
        
        logger.info(f"Dashboard loaded for {request.user.username}: {playbook_count} playbooks, {activity_count} activities")
        
        return render(request, 'dashboard.html', {
            'recent_playbooks': recent_playbooks,
            'recent_activities': recent_activities,
            'activity_count': activity_count,
            'playbook_count': playbook_count,
        })
        
    except Exception as e:
        logger.error(f"Error loading dashboard for {request.user.username}: {e}")
        # Return dashboard with empty data rather than error page
        return render(request, 'dashboard.html', {
            'recent_playbooks': [],
            'recent_activities': [],
            'activity_count': 0,
            'playbook_count': 0,
            'error_message': 'Unable to load some dashboard data'
        })


@login_required
def dashboard_activities(request):
    """
    HTMX endpoint for refreshing activity feed.
    
    Returns updated activity feed HTML fragment.
    
    Args:
        request: Django request object with optional 'hours' parameter
        
    Returns:
        HttpResponse: HTML fragment for activity feed
        
    Example:
        GET /dashboard/activities/?hours=24
    """
    logger.info(f"User {request.user.username} requested activity feed refresh")
    
    try:
        from methodology.services.activity_service import ActivityService
        
        # Get hours parameter (default to 24)
        hours = int(request.GET.get('hours', 24))
        
        # Get recent activities
        recent_activities = ActivityService.get_recent_activities(request.user, limit=10)
        
        logger.info(f"Returned {len(recent_activities)} activities for {request.user.username}")
        
        return render(request, 'methodology/partials/activity_feed.html', {
            'recent_activities': recent_activities,
        })
        
    except Exception as e:
        logger.error(f"Error refreshing activity feed for {request.user.username}: {e}")
        return render(request, 'methodology/partials/activity_feed.html', {
            'recent_activities': [],
        })


@login_required
def global_search(request):
    """Global search view for NAV-06.

    Delegates search logic to GlobalSearchService and renders consolidated
    results across Playbooks, Workflows, and Activities.
    
    Template: search/results.html
    Context:
        query: str - Search query entered by user
        playbooks: List[Playbook] - Matching playbooks
        workflows: List[Workflow] - Matching workflows
        activities: List[Activity] - Matching activities
        type_filter: str - Active type filter (playbooks/workflows/activities)
        status_filter: str - Active status filter (draft/active/released/disabled)
        source_filter: str - Active source filter (owned/downloaded)
    
    :param request: Django HttpRequest with GET parameters q, type, status, source
    :return: HttpResponse with rendered search results template
    """

    query = request.GET.get("q", "").strip()
    type_filter = request.GET.get("type") or ""
    status_filter = request.GET.get("status") or ""
    source_filter = request.GET.get("source") or ""

    filters = {}
    if type_filter:
        filters["type"] = type_filter
    if status_filter:
        filters["status"] = status_filter
    if source_filter:
        filters["source"] = source_filter

    logger.info(
        "Global search requested by %s with query='%s', filters=%s",
        request.user.username,
        query,
        filters,
    )

    service = GlobalSearchService()
    results = service.search(query=query, user=request.user, filters=filters)

    logger.info(
        "Global search completed for %s with query='%s': %d playbooks, %d workflows, %d activities",
        request.user.username,
        query,
        len(results["playbooks"]),
        len(results["workflows"]),
        len(results["activities"]),
    )

    return render(
        request,
        "search/results.html",
        {
            "query": query,
            "playbooks": results["playbooks"],
            "workflows": results["workflows"],
            "activities": results["activities"],
            "type_filter": type_filter,
            "status_filter": status_filter,
            "source_filter": source_filter,
        },
    )


@login_required
def global_search_suggestions(request):
    """Return HTML fragment with live global search suggestions.

    Designed for HTMX / AJAX usage from the navbar search input.
    
    Template: search/partials/suggestions.html
    Context:
        query: str - Search query entered by user
        playbooks: List[Playbook] - Top 5 matching playbooks
        workflows: List[Workflow] - Top 5 matching workflows
        activities: List[Activity] - Top 5 matching activities
    
    :param request: Django HttpRequest with GET parameter q
    :return: HttpResponse with rendered suggestions fragment
    """

    query = (request.GET.get("q", "") or "").strip()
    if not query:
        logger.info(
            "Global search suggestions requested by %s with empty query - returning empty fragment",
            request.user.username,
        )
        return render(
            request,
            "search/partials/suggestions.html",
            {
                "query": query,
                "playbooks": [],
                "workflows": [],
                "activities": [],
            },
        )

    logger.info("Global search suggestions requested by %s with query='%s'", request.user.username, query)

    service = GlobalSearchService()
    results = service.search(query=query, user=request.user, filters=None)

    # Limit suggestions per type to keep dropdown compact
    playbooks = list(results["playbooks"])[:5]
    workflows = list(results["workflows"])[:5]
    activities = list(results["activities"])[:5]

    logger.info(
        "Global search suggestions for %s with query='%s': %d playbooks, %d workflows, %d activities (limited)",
        request.user.username,
        query,
        len(playbooks),
        len(workflows),
        len(activities),
    )

    return render(
        request,
        "search/partials/suggestions.html",
        {
            "query": query,
            "playbooks": playbooks,
            "workflows": workflows,
            "activities": activities,
        },
    )
