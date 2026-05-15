import logging
from django.shortcuts import render

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared mock data
# ---------------------------------------------------------------------------

_STATUS_CSS = {
    "Draft": "bg-secondary",
    "Submitted": "bg-primary",
    "Processing (Galdr)": "bg-warning text-dark",
    "Reviewed": "pip-status-reviewed",
    "Accepted": "bg-success",
    "Rejected": "bg-danger",
}

_CHANGE_TYPE_CSS = {
    "ADD": "bg-success",
    "ALTER": "bg-warning text-dark",
    "DROP": "bg-danger",
}

MOCK_PIPS = [
    {
        "id": 42,
        "title": "Add Accessibility Audit",
        "target_playbook": "React Frontend Dev",
        "target_playbook_id": 1,
        "target_version": "v1.0",
        "changes_count": 1,
        "status": "Reviewed",
        "status_css": _STATUS_CSS["Reviewed"],
        "submitted": "2026-05-14",
        "last_updated": "2026-05-15",
        "submitted_by": "maria",
        "status_changed": True,
    },
    {
        "id": 38,
        "title": "State Management Patterns",
        "target_playbook": "React Frontend Dev",
        "target_playbook_id": 1,
        "target_version": "v1.0",
        "changes_count": 2,
        "status": "Accepted",
        "status_css": _STATUS_CSS["Accepted"],
        "submitted": "2026-04-20",
        "last_updated": "2026-04-22",
        "submitted_by": "maria",
        "status_changed": False,
    },
    {
        "id": 35,
        "title": "Drop Legacy IE Support",
        "target_playbook": "React Frontend Dev",
        "target_playbook_id": 1,
        "target_version": "v1.0",
        "changes_count": 1,
        "status": "Rejected",
        "status_css": _STATUS_CSS["Rejected"],
        "submitted": "2026-04-10",
        "last_updated": "2026-04-11",
        "submitted_by": "maria",
        "status_changed": False,
    },
    {
        "id": 30,
        "title": "Add Figma Integration Activity",
        "target_playbook": "UX Research",
        "target_playbook_id": 2,
        "target_version": "v2.1",
        "changes_count": 3,
        "status": "Draft",
        "status_css": _STATUS_CSS["Draft"],
        "submitted": "2026-03-05",
        "last_updated": "2026-03-05",
        "submitted_by": "maria",
        "status_changed": False,
    },
    {
        "id": 28,
        "title": "Improve Onboarding Flow",
        "target_playbook": "UX Research",
        "target_playbook_id": 2,
        "target_version": "v2.1",
        "changes_count": 1,
        "status": "Submitted",
        "status_css": _STATUS_CSS["Submitted"],
        "submitted": "2026-03-01",
        "last_updated": "2026-03-01",
        "submitted_by": "maria",
        "status_changed": False,
    },
    {
        "id": 27,
        "title": "Rename Discovery Activity",
        "target_playbook": "UX Research",
        "target_playbook_id": 2,
        "target_version": "v2.1",
        "changes_count": 1,
        "status": "Processing (Galdr)",
        "status_css": _STATUS_CSS["Processing (Galdr)"],
        "submitted": "2026-02-28",
        "last_updated": "2026-02-28",
        "submitted_by": "maria",
        "status_changed": False,
    },
]

MOCK_PIP_42 = {
    "id": 42,
    "title": "Add Accessibility Audit",
    "summary": "The React Frontend Dev playbook lacks WCAG 2.1 AA coverage. "
               "All components we build need accessibility checks but the playbook "
               "currently has no dedicated activity for it.",
    "target_playbook": "React Frontend Dev",
    "target_version": "v1.0",
    "target_playbook_id": 1,
    "status": "Reviewed",
    "status_css": _STATUS_CSS["Reviewed"],
    "submitted_by": "Maria Rodriguez",
    "submitted_at": "2026-05-14 09:00",
    "last_updated": "2026-05-15 08:00",
    "changes": [
        {
            "number": 1,
            "change_type": "ADD",
            "change_type_css": _CHANGE_TYPE_CSS["ADD"],
            "entity_type": "Activity",
            "name": "Accessibility Audit",
            "target_id": None,
            "target_name": None,
            "position": "After: Component Testing (id=22)",
            "content": (
                "Ensure all React components meet WCAG 2.1 AA standards.\n\n"
                "**Setup:** Install `axe-core` and `jest-axe`.\n\n"
                "**Tests:** Add `@axe-core/react` checks to each component's test suite. "
                "Configure the CI/CD pipeline to fail on any accessibility violation.\n\n"
                "**Checklist:**\n"
                "- [ ] All interactive elements keyboard-accessible\n"
                "- [ ] ARIA labels on icon-only buttons\n"
                "- [ ] Colour contrast ≥ 4.5:1\n"
                "- [ ] Focus trap in modals"
            ),
            "galdr_recommendation": "ACCEPT",
            "galdr_reasoning": (
                "Consistent with the Testing & Documentation workflow goal. "
                "No upstream or downstream conflicts detected. "
                "The new activity has a clear, well-defined position in the workflow."
            ),
            "admin_decision": None,
        },
        {
            "number": 2,
            "change_type": "ALTER",
            "change_type_css": _CHANGE_TYPE_CSS["ALTER"],
            "entity_type": "Activity",
            "name": None,
            "target_id": 22,
            "target_name": "Component Testing",
            "position": None,
            "content": (
                "Add `axe-core` a11y tests alongside existing Jest unit tests. "
                "Fail the build on any a11y violation reported by `jest-axe`. "
                "Update the Artifact link to include the new 'a11y-test-report' output."
            ),
            "galdr_recommendation": "REJECT",
            "galdr_reasoning": (
                "The proposed content removes the existing Artifact link to 'Test Suite', "
                "breaking the artifact dependency chain for Workflow 'Testing & Documentation'. "
                "Recommend rejecting until the author preserves the existing artifact link "
                "and appends the new one."
            ),
            "admin_decision": None,
        },
    ],
}

MOCK_PIP_30 = {
    "id": 30,
    "title": "Add Figma Integration Activity",
    "summary": "Our UX Research playbook covers discovery and testing but has no guidance "
               "on Figma handoff. This PIP adds three activities covering design token export, "
               "handoff checklist, and developer review session.",
    "target_playbook": "UX Research",
    "target_version": "v2.1",
    "target_playbook_id": 2,
    "status": "Draft",
    "status_css": _STATUS_CSS["Draft"],
    "submitted_by": "Maria Rodriguez",
    "submitted_at": None,
    "last_updated": "2026-03-05",
    "changes": [
        {
            "number": 1,
            "change_type": "ADD",
                "change_type_css": _CHANGE_TYPE_CSS["ADD"],
                "entity_type": "Activity",
                "name": "Export Design Tokens",
            "target_id": None,
            "target_name": None,
            "position": "Append at end of Workflow: Design Delivery",
            "content": "Export all design tokens from Figma using the Figma Tokens plugin.",
            "galdr_recommendation": None,
            "galdr_reasoning": None,
            "admin_decision": None,
        },
        {
            "number": 2,
            "change_type": "ADD",
                "change_type_css": _CHANGE_TYPE_CSS["ADD"],
                "entity_type": "Activity",
                "name": "Figma Handoff Checklist",
            "target_id": None,
            "target_name": None,
            "position": "After: Export Design Tokens",
            "content": "Run through the 12-item Figma handoff checklist before dev handoff.",
            "galdr_recommendation": None,
            "galdr_reasoning": None,
            "admin_decision": None,
        },
        {
            "number": 3,
            "change_type": "ALTER",
                "change_type_css": _CHANGE_TYPE_CSS["ALTER"],
                "entity_type": "Workflow",
            "name": None,
            "target_id": 5,
            "target_name": "Design Delivery",
            "position": None,
            "content": "Update workflow description to include Figma as the primary design tool.",
            "galdr_recommendation": None,
            "galdr_reasoning": None,
            "admin_decision": None,
        },
    ],
}

MOCK_PIP_38_ADMIN = {
    "id": 38,
    "title": "State Management Patterns",
    "summary": "Adds Redux Toolkit setup and patterns as a dedicated activity, "
               "and updates the existing Component Testing activity to cover store integration testing.",
    "target_playbook": "React Frontend Dev",
    "target_version": "v1.0",
    "target_playbook_id": 1,
    "status": "Reviewed",
    "status_css": _STATUS_CSS["Reviewed"],
    "submitted_by": "Maria Rodriguez",
    "submitted_at": "2026-04-20 14:30",
    "last_updated": "2026-04-21 10:00",
    "changes": [
        {
            "number": 1,
            "change_type": "ADD",
            "change_type_css": _CHANGE_TYPE_CSS["ADD"],
            "entity_type": "Activity",
            "name": "Redux Setup & Patterns",
            "target_id": None,
            "target_name": None,
            "position": "After: Create Components (id=21)",
            "content": (
                "Set up Redux Toolkit. Configure the store. "
                "Define typed hooks (useAppDispatch, useAppSelector). "
                "Document slice pattern and async thunk pattern."
            ),
            "galdr_recommendation": "ACCEPT",
            "galdr_reasoning": (
                "Directly addresses a known gap in the Component Development workflow. "
                "No conflicts with existing activities or artifacts."
            ),
            "admin_decision": "ACCEPT",
        },
        {
            "number": 2,
            "change_type": "ALTER",
            "change_type_css": _CHANGE_TYPE_CSS["ALTER"],
            "entity_type": "Activity",
            "name": None,
            "target_id": 22,
            "target_name": "Component Testing",
            "position": None,
            "content": (
                "Extend Component Testing to cover Redux store integration. "
                "Add section: 'Testing connected components with mock stores using @reduxjs/toolkit'."
            ),
            "galdr_recommendation": "ACCEPT",
            "galdr_reasoning": (
                "Augments existing activity without removing anything. "
                "Artifact links are preserved."
            ),
            "admin_decision": "ACCEPT",
        },
    ],
}


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

def pip_list(request):
    """FOB-PIP-LIST-1: My PIPs with filter bar, status badges, count pill."""
    logger.info("Mockup: pip_list | user=%s", getattr(request.user, "username", "anonymous"))
    statuses = list(_STATUS_CSS.items())
    context = {
        "pips": MOCK_PIPS,
        "pip_count": len(MOCK_PIPS),
        "unread_count": sum(1 for p in MOCK_PIPS if p["status_changed"]),
        "playbooks": ["React Frontend Dev", "UX Research"],
        "statuses": statuses,
        "is_admin": getattr(request.user, "is_staff", False),
        "active_page": "pips",
    }
    return render(request, "mockups/pips/list.html", context)


def pip_create(request):
    """FOB-PIP-CREATE-1: Create PIP with structured Change list."""
    logger.info("Mockup: pip_create | user=%s", getattr(request.user, "username", "anonymous"))
    context = {
        "target_playbook": "React Frontend Dev",
        "target_version": "v1.0",
        "target_playbook_id": 1,
        "released_playbooks": [
            {"id": 1, "name": "React Frontend Dev", "version": "v1.0"},
            {"id": 2, "name": "UX Research", "version": "v2.1"},
        ],
        "entity_types": ["Workflow", "Activity", "Skill", "Agent", "Artifact"],
        "change_types": ["ADD", "ALTER", "DROP"],
        "activities": [
            {"id": 20, "name": "Setup Project", "workflow": "Component Development"},
            {"id": 21, "name": "Create Components", "workflow": "Component Development"},
            {"id": 22, "name": "Component Testing", "workflow": "Testing & Documentation"},
            {"id": 23, "name": "Write Documentation", "workflow": "Testing & Documentation"},
        ],
        "workflows": [
            {"id": 10, "name": "Component Development"},
            {"id": 11, "name": "Testing & Documentation"},
        ],
        "draft_changes": [
            {
                "number": 1,
                "change_type": "ADD",
                "change_type_css": _CHANGE_TYPE_CSS["ADD"],
                "entity_type": "Activity",
                "name": "Accessibility Audit",
                "position": "After: Component Testing (id=22)",
                "content": "Ensure React components meet WCAG 2.1 AA standards…",
            }
        ],
        "active_page": "pips",
    }
    return render(request, "mockups/pips/create.html", context)


def pip_detail(request, pip_id):
    """FOB-PIP-DETAIL-1: View a PIP with Galdr recommendations."""
    logger.info("Mockup: pip_detail | pip_id=%s | user=%s", pip_id, getattr(request.user, "username", "anonymous"))
    pip = MOCK_PIP_30 if pip_id == 30 else MOCK_PIP_42
    context = {
        "pip": pip,
        "active_page": "pips",
    }
    return render(request, "mockups/pips/detail.html", context)


def pip_admin_review(request, pip_id):
    """FOB-PIP-ADMIN-1: Admin reviews Galdr recommendations and makes decisions."""
    logger.info("Mockup: pip_admin_review | pip_id=%s | user=%s", pip_id, getattr(request.user, "username", "anonymous"))
    context = {
        "pip": MOCK_PIP_38_ADMIN,
        "active_page": "pips",
    }
    return render(request, "mockups/pips/admin_review.html", context)
