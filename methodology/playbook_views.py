"""
Playbook views for CRUDV operations.

Provides views for listing, creating, viewing, editing, and deleting playbooks.
Includes a 3-step creation wizard and export/import functionality.
"""

import json
import logging
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from methodology.forms.playbook_forms import (
    PlaybookBasicInfoForm,
    PlaybookPublishingForm,
    PlaybookWorkflowForm,
)
from methodology.models import Playbook
from methodology.services.playbook_service import PlaybookService
from methodology.utils.playbook_access import playbook_readable_or_404
from methodology.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)

# ─── NO ORM IN VIEWS ────────────────────────────────────────────────────────
# Views are thin controllers. NEVER query the ORM directly here.
# All data access must go through services in methodology/services/.
# Both views and MCP tools drink from the same service well.
# ────────────────────────────────────────────────────────────────────────────


def _wizard_skip_requested(post_data) -> bool:
    """Return True when Step 2 POST explicitly skips workflow creation."""
    raw = (post_data.get("skip") or "").strip().lower()
    return raw in ("true", "1", "on", "yes")


def _workflows_from_step2_form(cleaned_data: dict, *, skipped: bool) -> list[dict]:
    """Build session-safe workflow payloads from Step 2 form data."""
    if skipped:
        return []
    name = (cleaned_data.get("workflow_name") or "").strip()
    if not name:
        return []
    description = (cleaned_data.get("workflow_description") or "").strip()
    return [{"name": name, "description": description}]


def _create_wizard_workflows(playbook: Playbook, workflows_data: list) -> None:
    """Persist workflows collected during the creation wizard."""
    for index, item in enumerate(workflows_data, start=1):
        if isinstance(item, dict):
            name = (item.get("name") or "").strip()
            description = (item.get("description") or "").strip()
        else:
            name = str(item).strip()
            description = ""
        if not name:
            continue
        WorkflowService.create_workflow(
            playbook,
            name=name,
            description=description,
            order=index,
        )
        logger.info(
            "Wizard created workflow %r for playbook id=%s order=%s",
            name,
            playbook.pk,
            index,
        )


# ==================== LIST ====================


@login_required
def playbook_list(request):
    """
    List playbooks visible to the current user (owned + public by others + team-shared).

    Template: playbooks/list.html
    Context:
        playbooks — owned playbooks
        public_playbooks — other authors' public, non-draft playbooks
        team_playbooks — playbooks shared via team membership
        has_playbooks — True when any list is non-empty

    :param request: Django request object
    :return: Rendered list template
    """
    playbooks = PlaybookService.list_playbooks(author=request.user)
    public_playbooks = PlaybookService.list_public_playbooks(request.user)
    team_playbooks = PlaybookService.list_team_playbooks_for_user(request.user)
    has_playbooks = bool(playbooks or public_playbooks or team_playbooks)
    logger.info(
        "User %s viewing playbook list (%s owned, %s public by others, %s team, has_any=%s)",
        request.user.username,
        len(playbooks),
        len(public_playbooks),
        len(team_playbooks),
        has_playbooks,
    )
    return render(
        request,
        "playbooks/list.html",
        {
            "playbooks": playbooks,
            "public_playbooks": public_playbooks,
            "team_playbooks": team_playbooks,
            "has_playbooks": has_playbooks,
        },
    )


# ==================== CREATE WIZARD ====================


@login_required
def playbook_create(request):
    """
    Step 1 of the playbook creation wizard (basic info).

    GET: Render step-1 form.
    POST: Validate and store in session; redirect to step 2.

    :param request: Django request object
    :return: Rendered step-1 form or redirect
    """
    if request.method == "POST":
        form = PlaybookBasicInfoForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data["name"]

            # Check for duplicate name (requires user context, not in form)
            if PlaybookService.author_has_playbook_named(request.user, name):
                form.add_error("name", "A playbook with this name already exists")
                return render(
                    request, "playbooks/create_wizard_step1.html", {"form": form}
                )

            wizard_data = {
                "name": name,
                "description": form.cleaned_data["description"],
                "category": form.cleaned_data["category"],
                "visibility": form.cleaned_data.get("visibility", "private"),
                "tags": form.cleaned_data.get("tags", []),
            }
            request.session["wizard_data"] = wizard_data
            logger.info(
                f"Playbook wizard step 1 completed by {request.user.username}: '{name}'"
            )
            return redirect("playbook_create_step2")

        return render(request, "playbooks/create_wizard_step1.html", {"form": form})

    form = PlaybookBasicInfoForm()
    return render(request, "playbooks/create_wizard_step1.html", {"form": form})


@login_required
def playbook_create_step2(request):
    """
    Step 2 of the creation wizard (optional workflows).

    GET: Render step-2 form.
    POST: Store workflows in session; redirect to step 3.

    :param request: Django request object
    :return: Rendered step-2 form or redirect
    """
    wizard_data = request.session.get("wizard_data")
    if not wizard_data:
        return redirect("playbook_create")

    if request.method == "POST":
        form = PlaybookWorkflowForm(request.POST)
        if form.is_valid():
            skipped = _wizard_skip_requested(request.POST) or form.cleaned_data.get(
                "skip"
            )
            wizard_data["workflows"] = _workflows_from_step2_form(
                form.cleaned_data,
                skipped=skipped,
            )
            request.session["wizard_data"] = wizard_data
            logger.info(
                "Playbook wizard step 2 completed by %s: workflows=%s",
                request.user.username,
                len(wizard_data["workflows"]),
            )
            return redirect("playbook_create_step3")
        logger.warning(
            "Playbook wizard step 2 validation failed for %s: %s",
            request.user.username,
            form.errors,
        )
        return render(
            request,
            "playbooks/create_wizard_step2.html",
            {
                "wizard_data": wizard_data,
                "form": form,
            },
        )

    return render(
        request,
        "playbooks/create_wizard_step2.html",
        {
            "wizard_data": wizard_data,
            "form": PlaybookWorkflowForm(),
        },
    )


@login_required
def playbook_create_step3(request):
    """
    Step 3 (review and submit) of the creation wizard.

    GET: Show review/summary page.
    POST: Create the playbook and redirect to detail.

    :param request: Django request object
    :return: Rendered step-3 form or redirect to detail
    """
    wizard_data = request.session.get("wizard_data")
    if not wizard_data:
        return redirect("playbook_create")

    form = PlaybookPublishingForm()

    if request.method == "POST":
        form = PlaybookPublishingForm(request.POST)
        status = None
        if form.is_valid():
            status = form.cleaned_data["status"]
        elif request.POST.get("status") == "active":
            # Legacy clients/tests may still POST active (not shown in wizard UI).
            status = "active"
            logger.info(
                "Playbook wizard step 3 using legacy status=active for %s",
                request.user.username,
            )
        else:
            return render(
                request,
                "playbooks/create_wizard_step3.html",
                {"wizard_data": wizard_data, "form": form},
            )
        try:
            playbook = PlaybookService.create_playbook(
                name=wizard_data["name"],
                description=wizard_data["description"],
                category=wizard_data["category"],
                author=request.user,
                status=status,
                visibility=wizard_data.get("visibility", "private"),
            )
            if wizard_data.get("tags"):
                playbook.tags = wizard_data["tags"]
                playbook.save()

            _create_wizard_workflows(playbook, wizard_data.get("workflows") or [])

            del request.session["wizard_data"]
            messages.success(
                request, f"Playbook '{playbook.name}' created successfully!"
            )
            logger.info(
                f"Playbook '{playbook.name}' (id={playbook.pk}) created by {request.user.username}"
            )
            return redirect("playbook_detail", pk=playbook.pk)

        except ValidationError as e:
            messages.error(request, str(e.message))
            return render(
                request,
                "playbooks/create_wizard_step3.html",
                {"wizard_data": wizard_data, "form": form},
            )

    return render(
        request,
        "playbooks/create_wizard_step3.html",
        {"wizard_data": wizard_data, "form": form},
    )


# ==================== LEGACY ====================


@login_required
def playbook_add(request):
    """Legacy redirect to new creation wizard."""
    return redirect("playbook_create")


# ==================== DETAIL ====================


@login_required
def playbook_detail(request, pk):
    """
    Display playbook detail with Overview and Workflows tabs.

    Template: playbooks/detail.html
    Context: playbook, workflows, quick_stats, can_edit

    :param request: Django request object
    :param pk: Playbook primary key
    :return: Rendered detail template
    """
    playbook = playbook_readable_or_404(request, pk)
    workflows = WorkflowService.get_workflows_for_playbook(playbook.pk)
    quick_stats = playbook.get_quick_stats()
    can_edit = playbook.can_edit(request.user)

    from methodology.services.agent_service import AgentService

    agents = AgentService.list_agents_for_playbook(playbook.pk)
    from methodology.services.phase_service import PhaseService

    phases = PhaseService.list_phases(playbook.pk, request.user)
    logger.info(
        f"User {request.user.username} viewing playbook '{playbook.name}' (id={pk})"
    )

    from methodology.services.playbook_history_service import list_playbook_version_rows

    context = {
        "playbook": playbook,
        "workflows": workflows,
        "quick_stats": quick_stats,
        "can_edit": can_edit,
        "agents": agents,
        "phases": phases,
        "version_history": list_playbook_version_rows(playbook),
    }
    if request.GET.get("embed") == "1":
        return render(request, "playbooks/_embed.html", context)
    return render(request, "playbooks/detail.html", context)


@login_required
def playbook_version_snapshot(request, pk, version_slug):
    """Pretty-print one historical ``PlaybookVersion.snapshot_data`` (S13)."""
    playbook = playbook_readable_or_404(request, pk)
    vn = Decimal(str(version_slug.replace("_", ".")))

    from methodology.services.playbook_history_service import (
        get_playbook_version_by_number,
    )

    pv = get_playbook_version_by_number(playbook, vn)
    if pv is None:
        raise Http404("Version snapshot not found")

    snapshot_raw = json.dumps(pv.snapshot_data, indent=2, sort_keys=True, default=str)
    return render(
        request,
        "playbooks/version_snapshot.html",
        {
            "playbook": playbook,
            "record": pv,
            "snapshot_json": snapshot_raw,
        },
    )


@login_required
def playbook_versions_compare(request, pk):
    """Split view of two snapshots (JSON) for HISTORY compare (S14)."""
    playbook = playbook_readable_or_404(request, pk)
    left_slug = request.GET.get("left", "").strip()
    right_slug = request.GET.get("right", "").strip()
    if not left_slug or not right_slug:
        raise Http404("Query params left and right (e.g. 1_0) are required")

    from methodology.services.playbook_history_service import (
        get_playbook_version_by_number,
    )

    v_left = Decimal(str(left_slug.replace("_", ".")))
    v_right = Decimal(str(right_slug.replace("_", ".")))
    pv_a = get_playbook_version_by_number(playbook, v_left)
    pv_b = get_playbook_version_by_number(playbook, v_right)
    if pv_a is None or pv_b is None:
        raise Http404("One or both snapshots are missing")

    left_json = json.dumps(pv_a.snapshot_data, indent=2, sort_keys=True, default=str)
    right_json = json.dumps(pv_b.snapshot_data, indent=2, sort_keys=True, default=str)

    return render(
        request,
        "playbooks/version_compare.html",
        {
            "playbook": playbook,
            "left_label": format(v_left, "f"),
            "right_label": format(v_right, "f"),
            "left_json": left_json,
            "right_json": right_json,
        },
    )


# ==================== EDIT ====================


@login_required
def playbook_edit(request, pk):
    """
    Edit a playbook.

    GET: Render edit form with current values.
    POST: Validate and update; redirect to detail on success.

    :param request: Django request object
    :param pk: Playbook primary key
    :return: Rendered edit form or redirect
    """
    playbook = get_object_or_404(Playbook, pk=pk)

    if not playbook.can_edit(request.user):
        messages.error(request, "You don't have permission to edit this playbook.")
        return redirect("playbook_detail", pk=pk)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        category = request.POST.get("category", "").strip()
        visibility = request.POST.get("visibility", "").strip()
        tags_raw = request.POST.get("tags", "").strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

        if not name:
            return render(
                request,
                "playbooks/edit.html",
                {
                    "playbook": playbook,
                    "errors": {"name": "Name is required"},
                    "form_data": request.POST,
                    "tags_string": tags_raw,
                },
            )

        try:
            PlaybookService.update_playbook(
                pk,
                name=name,
                description=description,
                category=category,
                visibility=visibility,
                tags=tags,
            )
            messages.success(request, f"Playbook '{name}' updated successfully!")
            logger.info(f"Playbook {pk} updated by {request.user.username}")
            return redirect("playbook_detail", pk=pk)
        except ValidationError as e:
            err_msg = e.messages[0] if getattr(e, "messages", None) else str(e)
            return render(
                request,
                "playbooks/edit.html",
                {
                    "playbook": playbook,
                    "errors": {"name": err_msg},
                    "form_data": request.POST,
                    "tags_string": request.POST.get("tags", ""),
                },
            )

    return render(
        request,
        "playbooks/edit.html",
        {
            "playbook": playbook,
            "errors": {},
            "form_data": {},
            "tags_string": ", ".join(playbook.tags) if playbook.tags else "",
        },
    )


# ==================== DELETE ====================


@login_required
def playbook_delete_confirm(request, pk):
    """
    Return delete confirmation modal partial (loaded via HTMX).

    :param request: Django request object
    :param pk: Playbook primary key
    :return: Rendered modal partial
    """
    playbook = get_object_or_404(Playbook, pk=pk)

    if not playbook.is_owned_by(request.user):
        messages.error(request, "You don't have permission to delete this playbook.")
        return redirect("playbook_list")

    return render(request, "playbooks/delete_modal.html", {"playbook": playbook})


@login_required
def playbook_delete(request, pk):
    """
    Delete a playbook (POST only). GET redirects to detail.

    :param request: Django request object
    :param pk: Playbook primary key
    :return: Redirect to playbook list (on POST) or detail (on GET)
    """
    playbook = get_object_or_404(Playbook, pk=pk)

    if request.method != "POST":
        return redirect("playbook_detail", pk=pk)

    if not playbook.is_owned_by(request.user):
        messages.error(request, "You don't have permission to delete this playbook.")
        return redirect("playbook_list")

    name = playbook.name
    PlaybookService.delete_playbook(pk)
    messages.success(request, f"Playbook '{name}' deleted successfully.")
    logger.info(f"Playbook '{name}' (id={pk}) deleted by {request.user.username}")
    return redirect("playbook_list")


# ==================== ACTIONS ====================


@login_required
@require_POST
def playbook_release(request, pk):
    """
    Confirm release: draft → released next major line, or released → next major line.

    POST body ``release_description`` is required.

    """
    get_object_or_404(Playbook, pk=pk)
    description = request.POST.get("release_description", "")

    try:
        PlaybookService.release_playbook(pk, request.user, description=description)
    except PermissionError:
        messages.error(request, "You don't have permission to release this playbook.")
    except ValidationError as e:
        if getattr(e, "error_dict", None):
            for errs in e.error_dict.values():
                for msg in errs:
                    messages.error(request, str(msg))
        elif getattr(e, "messages", False):
            for msg in e.messages:
                messages.error(request, msg)
        else:
            messages.error(request, str(e.message))
    else:
        messages.success(request, "Playbook released.")

    logger.info(f"Release POST for playbook id={pk} by {request.user.username}")
    return redirect("playbook_detail", pk=pk)


@login_required
def playbook_export(request, pk):
    """
    Export playbook as JSON (download).

    :param request: Django request object
    :param pk: Playbook primary key
    :return: JSON file download response
    """
    from django.http import JsonResponse
    from django.utils.text import slugify

    playbook = get_object_or_404(Playbook, pk=pk)
    if not playbook.is_owned_by(request.user):
        messages.error(request, "You don't have permission to export this playbook.")
        logger.info(
            "User %s denied export on playbook id=%s (not owner)",
            request.user.username,
            pk,
        )
        return redirect("playbook_list")

    logger.info(f"User {request.user.username} exporting playbook {pk}")

    data = {
        "id": playbook.pk,
        "name": playbook.name,
        "description": playbook.description,
        "category": playbook.category,
        "version": str(playbook.version),
        "status": playbook.status,
    }
    filename = f"{slugify(playbook.name)}.json"
    response = JsonResponse(data)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def playbook_duplicate(request, pk):
    """
    Duplicate a playbook. Accepts optional new_name in POST body.

    :param request: Django request object
    :param pk: Playbook primary key
    :return: Redirect to new playbook
    """
    playbook = get_object_or_404(Playbook, pk=pk)
    new_name = (
        request.POST.get("new_name", f"Copy of {playbook.name}").strip()
        or f"Copy of {playbook.name}"
    )

    try:
        duplicate = PlaybookService.duplicate_playbook(pk, new_name, request.user)
        messages.success(request, f"Playbook duplicated as '{duplicate.name}'.")
        return redirect("playbook_detail", pk=duplicate.pk)
    except ValidationError as e:
        messages.error(request, str(e.message))
        return redirect("playbook_detail", pk=pk)


@login_required
def playbook_toggle_status(request, pk):
    """
    Toggle playbook status between active and disabled.

    :param request: Django request object
    :param pk: Playbook primary key
    :return: Redirect to playbook detail
    """
    playbook = get_object_or_404(Playbook, pk=pk)

    if not playbook.is_owned_by(request.user):
        messages.error(
            request, "You don't have permission to change this playbook's status."
        )
        return redirect("playbook_detail", pk=pk)

    new_status = "disabled" if playbook.status == "active" else "active"
    PlaybookService.update_playbook(pk, status=new_status)
    messages.success(request, f"Playbook status changed to '{new_status}'.")
    logger.info(
        f"Playbook {pk} status toggled to {new_status} by {request.user.username}"
    )
    return redirect("playbook_detail", pk=pk)


# ==================== PRIVATE HELPERS (none currently) ====================
