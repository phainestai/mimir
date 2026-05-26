"""
Views for publicly-accessible legal documents: Privacy Policy and User Agreement.

Each document is served as:
  • An HTML page (extends base.html) — for in-browser reading.
  • A PDF download — generated on-demand via WeasyPrint.
"""

import logging

from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
import weasyprint

logger = logging.getLogger(__name__)


def privacy_policy(request):
    """Render the Privacy Policy as an HTML page."""
    logger.info("Privacy Policy page accessed from %s", _client_ip(request))
    return render(request, "legal/privacy_policy.html")


def privacy_policy_pdf(request):
    """Stream the Privacy Policy as a downloadable PDF (generated via WeasyPrint)."""
    logger.info("Privacy Policy PDF download requested from %s", _client_ip(request))
    return _render_pdf(
        request,
        template="legal/privacy_policy_pdf.html",
        filename="mimir_privacy_policy.pdf",
    )


def user_agreement(request):
    """Render the User Agreement as an HTML page."""
    logger.info("User Agreement page accessed from %s", _client_ip(request))
    return render(request, "legal/user_agreement.html")


def user_agreement_pdf(request):
    """Stream the User Agreement as a downloadable PDF (generated via WeasyPrint)."""
    logger.info("User Agreement PDF download requested from %s", _client_ip(request))
    return _render_pdf(
        request,
        template="legal/user_agreement_pdf.html",
        filename="mimir_user_agreement.pdf",
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _render_pdf(request, *, template: str, filename: str) -> HttpResponse:
    """Render *template* to PDF bytes via WeasyPrint and return as an HTTP download.

    PDF templates are standalone HTML (no base.html); they are rendered without
    the request so Django's context processors (which need request.user) are not
    invoked.
    """
    html_string = render_to_string(template)
    logger.debug("Generating PDF from template '%s'", template)
    pdf_bytes = (
        weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri("/"))
        .write_pdf()
    )
    logger.info("PDF generated: %s (%d bytes)", filename, len(pdf_bytes))
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _client_ip(request) -> str:
    """Extract client IP from request for logging."""
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")
