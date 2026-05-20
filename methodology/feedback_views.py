"""HTTP views for the global feedback / bug-report widget."""

from __future__ import annotations

import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from methodology.services.bug_report_service import BugReportService

logger = logging.getLogger(__name__)


@login_required
@require_POST
def submit_feedback(request: HttpRequest) -> HttpResponse:
    """
    Accept HTMX POST from the offcanvas bug widget.

    Reporter email is always the authenticated user's account email (no form field).

    :param request: POST with description, page_url, form_data, app_version
    :returns: HTML fragment for swap, or 400 with error fragment
    """
    description = (request.POST.get("description") or "").strip()
    reporter_email = (getattr(request.user, "email", None) or "").strip()
    page_url = (request.POST.get("page_url") or "").strip()
    form_data = (request.POST.get("form_data") or "").strip()
    client_version = (request.POST.get("app_version") or "").strip()
    logger.info(
        "submit_feedback user=%s authenticated=%s page=%s client_ver=%s len_desc=%s",
        getattr(request.user, "pk", None),
        request.user.is_authenticated,
        page_url or request.path,
        client_version,
        len(description),
    )

    if not description:
        return HttpResponse(
            render_to_string(
                "methodology/feedback_submit_result.html",
                {"ok": False, "message": "Please describe what went wrong."},
                request=request,
            ),
            status=200,
        )
    if not reporter_email:
        return HttpResponse(
            render_to_string(
                "methodology/feedback_submit_result.html",
                {
                    "ok": False,
                    "message": (
                        "Your profile has no email address. Add one in your account settings "
                        "so we can follow up on reports."
                    ),
                },
                request=request,
            ),
            status=200,
        )

    try:
        result = BugReportService.submit_bug(
            description,
            reporter_email,
            source="ui",
            page_url=page_url,
            form_data=form_data,
        )
    except ValueError as e:
        logger.warning("submit_feedback validation/service error: %s", e)
        return HttpResponse(
            render_to_string(
                "methodology/feedback_submit_result.html",
                {"ok": False, "message": str(e)},
                request=request,
            ),
            status=200,
        )

    logger.info(
        "submit_feedback success issue_number=%s url=%s",
        result.get("issue_number"),
        result.get("issue_url"),
    )
    return HttpResponse(
        render_to_string(
            "methodology/feedback_submit_result.html",
            {
                "ok": True,
                "message": "Thank you — your report was submitted.",
                "issue_url": result.get("issue_url"),
            },
            request=request,
        )
    )
