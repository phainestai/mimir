"""
Read-only playbook version history projections for playbook detail and derivatives.
"""

from __future__ import annotations

from decimal import Decimal

from django.db.models import QuerySet

from methodology.models import Playbook, PlaybookVersion


def playbook_versions_ordered(playbook: Playbook) -> QuerySet[PlaybookVersion]:
    return (
        playbook.versions.select_related("pip")
        .order_by("-version_number", "-created_at")
        .all()
    )


def list_playbook_version_rows(playbook: Playbook) -> list[dict]:
    """
    Build template-friendly rows: version label, major/minor, source text, descriptions, pip id.
    """
    rows = []
    for v in playbook_versions_ordered(playbook):
        rows.append(
            {
                "version_number": v.version_number,
                "label": format(v.version_number, "f"),
                "url_slug": str(v.version_number).replace(".", "_"),
                "kind_major": bool(v.is_major),
                "source": str(v.source),
                "description": v.description.strip() if v.description else "",
                "change_summary": v.change_summary.strip() if v.change_summary else "",
                "pip_id": v.pip_id,
            }
        )
    return rows


def get_playbook_version_by_number(
    playbook: Playbook, version_number: Decimal
) -> PlaybookVersion | None:
    return (
        PlaybookVersion.objects.filter(playbook=playbook, version_number=version_number)
        .select_related("pip")
        .first()
    )
