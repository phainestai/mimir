"""PIP (Act 9) UI views — list, create, draft edit, preview, submit."""

from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import RedirectView

from methodology.models import PipChange, ProcessImprovementProposal as PipModel

logger = logging.getLogger(__name__)


def _format_validation_error(exc: ValidationError) -> str:
    if hasattr(exc, "messages"):
        return "; ".join(str(m) for m in exc.messages)
    return str(exc)


def _pip_edit_query_suffix(request) -> str:
    """Preserve workflow/activity context across redirects (?workflow=&activity=)."""
    wf = request.GET.get("workflow") or request.POST.get("focus_workflow")
    act = request.GET.get("activity") or request.POST.get("focus_activity")
    parts = []
    if wf and str(wf).isdigit():
        parts.append(f"workflow={int(wf)}")
    if act and str(act).isdigit():
        parts.append(f"activity={int(act)}")
    return ("?" + "&".join(parts)) if parts else ""


def _pip_edit_suffix_from_focus(wf_id: int | None, act_id: int | None) -> str:
    parts = []
    if wf_id is not None:
        parts.append(f"workflow={wf_id}")
    if act_id is not None:
        parts.append(f"activity={act_id}")
    return ("?" + "&".join(parts)) if parts else ""


def _validated_pip_focus_ids(pip, request) -> tuple[int | None, int | None]:
    wf_raw = request.GET.get("workflow")
    act_raw = request.GET.get("activity")
    wf_id = int(wf_raw) if wf_raw and str(wf_raw).isdigit() else None
    act_id = int(act_raw) if act_raw and str(act_raw).isdigit() else None
    from methodology.models import Activity, Workflow

    if wf_id is not None and not Workflow.objects.filter(pk=wf_id, playbook=pip.playbook).exists():
        wf_id = None
    if act_id is not None:
        act = Activity.objects.filter(pk=act_id, workflow__playbook=pip.playbook).first()
        if act is None:
            act_id = None
        elif wf_id is not None and act.workflow_id != wf_id:
            act_id = None
    return wf_id, act_id


def _resolve_create_prefill_workflow(request, prefill_playbook_id: int | None):
    """Apply ?workflow= to create form; returns (playbook_pk, workflow_pk_or_none, workflow_or_none)."""
    from methodology.models import Workflow

    wf_raw = request.GET.get("workflow")
    if not wf_raw or not str(wf_raw).isdigit():
        return prefill_playbook_id, None, None

    wf_id = int(wf_raw)
    wf_obj = Workflow.objects.select_related("playbook").filter(pk=wf_id).first()
    if not wf_obj:
        messages.warning(request, "Unknown workflow.")
        return prefill_playbook_id, None, None

    pb = wf_obj.playbook
    if pb.status != "released":
        messages.warning(request, "PIPs apply only to Released playbooks.")
        return prefill_playbook_id, None, None
    if pb.source != "owned" or pb.author_id != request.user.id:
        messages.warning(
            request,
            "You can only start a workflow-scoped PIP on playbooks you own.",
        )
        return prefill_playbook_id, None, None

    if prefill_playbook_id is not None and prefill_playbook_id != pb.pk:
        messages.warning(
            request,
            "That workflow does not belong to the playbook in the URL.",
        )
        return prefill_playbook_id, None, None

    logger.info(
        "PIP create workflow hint wf=%s playbook=%s user=%s",
        wf_id,
        pb.pk,
        request.user.username,
    )
    return pb.pk, wf_id, wf_obj


def _resolve_create_prefill_activity(
    request, playbook_id: int | None, workflow_id: int | None
):
    """Validate ?activity= against playbook/workflow hints from playbook/workflow detail."""
    from methodology.models import Activity

    raw = request.GET.get("activity")
    if not raw or not str(raw).isdigit():
        return None, None
    aid = int(raw)
    act = Activity.objects.select_related("workflow__playbook").filter(pk=aid).first()
    if act is None:
        messages.warning(request, "Unknown activity.")
        return None, None

    pb = act.workflow.playbook
    if pb.status != "released":
        messages.warning(request, "PIPs apply only to Released playbooks.")
        return None, None
    if pb.source != "owned" or pb.author_id != request.user.id:
        messages.warning(
            request,
            "You can only start an activity-scoped PIP on playbooks you own.",
        )
        return None, None
    if playbook_id is not None and playbook_id != pb.pk:
        messages.warning(
            request,
            "That activity does not belong to the playbook in the URL.",
        )
        return None, None
    if workflow_id is not None and act.workflow_id != workflow_id:
        messages.warning(
            request,
            "That activity does not belong to the workflow in the URL.",
        )
        return None, None

    logger.info(
        "PIP create activity hint act=%s wf=%s playbook=%s user=%s",
        aid,
        act.workflow_id,
        pb.pk,
        request.user.username,
    )
    return aid, act


PIP_DETAIL_STATIC_BANNERS = {
    PipModel.STATUS_DRAFT: "Draft — not yet submitted for review.",
    PipModel.STATUS_SUBMITTED: "Submitted — awaiting Galdr processing.",
    PipModel.STATUS_PROCESSING_GALDR: (
        "Galdr is reviewing your changes — check back shortly."
    ),
    PipModel.STATUS_REVIEWED: "Reviewed — awaiting Administrator decision.",
}


def _pip_detail_status_banner(pip) -> str:
    """Banner copy aligned with act-9 view scenarios."""
    st = pip.status
    if st in PIP_DETAIL_STATIC_BANNERS:
        return PIP_DETAIL_STATIC_BANNERS[st]
    if st == PipModel.STATUS_ACCEPTED:
        return (
            f"Accepted — all changes applied. {pip.playbook.name} "
            f"is now v{pip.playbook.version}."
        )
    if st == PipModel.STATUS_ACCEPTED_PARTIAL:
        qs = list(pip.changes.all())
        accepted_n = sum(
            1 for ch in qs if ch.admin_decision == PipChange.ADMIN_ACCEPT
        )
        return (
            f"Partially accepted — {accepted_n} of {len(qs)} changes applied. "
            f"{pip.playbook.name} is now v{pip.playbook.version}."
        )
    if st == PipModel.STATUS_REJECTED:
        return "Rejected — no changes were applied."
    return ""


def _pip_detail_context(pip, user):
    change_count = pip.changes.count()
    withdrawable = pip.status in {
        PipModel.STATUS_DRAFT,
        PipModel.STATUS_SUBMITTED,
        PipModel.STATUS_PROCESSING_GALDR,
    }
    banner = _pip_detail_status_banner(pip)
    can_submit = pip.status in {
        PipModel.STATUS_DRAFT,
        PipModel.STATUS_SUBMITTED,
    } and change_count > 0 and pip.created_by_id == user.pk
    submit_label = (
        "Re-submit for Galdr review"
        if pip.status == PipModel.STATUS_SUBMITTED
        else "Submit for review"
    )

    ctx = {
        "pip": pip,
        "status_banner": banner,
        "can_edit": pip.status == PipModel.STATUS_DRAFT and pip.created_by_id == user.pk,
        "can_submit": bool(can_submit),
        "submit_label": submit_label,
        "can_withdraw": withdrawable and pip.created_by_id == user.pk,
        "can_preview": True,
        "admin_review_url": None,
    }
    if (
        getattr(user, "is_staff", False)
        and pip.status == PipModel.STATUS_REVIEWED
    ):
        try:
            base = reverse("pip_admin_review", kwargs={"pk": pip.pk})
            ctx["admin_review_url"] = base
        except Exception:  # noqa: BLE001
            logger.exception("PIP admin URL unavailable pk=%s", pip.pk)

    logger.info(
        "PIP detail context pk=%s user=%s can_submit=%s can_edit=%s",
        pip.pk,
        getattr(user, "username", ""),
        ctx["can_submit"],
        ctx["can_edit"],
    )
    return ctx


PIP_LIST_STATUS_CHOICES = [
    ("draft", "Draft"),
    ("submitted", "Submitted"),
    ("processing_galdr", "Processing (Galdr)"),
    ("reviewed", "Reviewed"),
    ("accepted", "Accepted"),
    ("accepted_partial", "Partially accepted"),
    ("rejected", "Rejected"),
]


def _pip_list_params(request):
    scope = request.GET.get("scope", "mine")
    if scope not in {"mine", "all"}:
        scope = "mine"
    status_filters = request.GET.getlist("status")
    playbook_raw = request.GET.get("playbook")
    playbook_pk = (
        int(playbook_raw)
        if playbook_raw and str(playbook_raw).isdigit()
        else None
    )
    return scope, status_filters, playbook_pk


class PipListLegacyRedirect(RedirectView):
    pattern_name = "pip_list"
    permanent = False


@login_required
def pip_list(request):
    from methodology.models import Playbook
    from methodology.services.pip_service import PIPService

    scope, status_filters, playbook_pk = _pip_list_params(request)
    logger.info(
        "User %s opening PIP list scope=%s statuses=%s playbook=%s",
        request.user.username,
        scope,
        status_filters,
        playbook_pk,
    )
    last_visit = PIPService.last_list_visit_at(request.user)
    try:
        queryset = PIPService.list_queryset_for_user(
            actor=request.user,
            scope=scope,
            status_filters=status_filters or None,
            playbook_id=playbook_pk,
        )
    except PermissionError:
        messages.warning(request, "You do not have permission to view all PIPs.")
        scope = "mine"
        queryset = PIPService.list_queryset_for_user(
            actor=request.user,
            scope="mine",
            status_filters=status_filters or None,
            playbook_id=playbook_pk,
        )
    rows = [
        {"pip": pip, "unread_dot": pip.status_changed_since_visit(last_visit)}
        for pip in queryset
    ]
    filter_ids = queryset.values_list("playbook_id", flat=True).distinct()
    filter_playbooks = Playbook.objects.filter(pk__in=filter_ids).order_by("name")
    pip_count = len(rows)
    PIPService.mark_list_viewed(request.user)
    return render(
        request,
        "pips/list.html",
        {
            "pip_rows": rows,
            "pip_count": pip_count,
            "list_scope": scope,
            "status_filters": status_filters,
            "filter_playbooks": filter_playbooks,
            "selected_playbook": playbook_pk,
            "pip_status_choices": PIP_LIST_STATUS_CHOICES,
        },
    )


@login_required
def pip_detail(request, pk: int):
    from methodology.services.pip_service import PIPService

    pip = PIPService.get_pip_with_changes(pk, request.user)
    logger.info(
        "User %s viewing PIP detail pk=%s status=%s",
        request.user.username,
        pk,
        pip.status,
    )
    return render(request, "pips/detail.html", _pip_detail_context(pip, request.user))


@login_required
def pip_create(request):
    from methodology.models import Activity, Playbook, Workflow
    from methodology.services.pip_service import PIPService

    released = Playbook.objects.filter(status="released").order_by("name")

    prefill_raw = request.GET.get("playbook")
    prefill_id = int(prefill_raw) if prefill_raw and str(prefill_raw).isdigit() else None

    pb_pre = Playbook.objects.filter(pk=prefill_id).first() if prefill_id else None
    if prefill_id and (
        pb_pre is None
        or pb_pre.status != "released"
        or pb_pre.source != "owned"
        or pb_pre.author_id != request.user.id
    ):
        messages.warning(request, "Invalid or inaccessible playbook for PIP creation.")
        prefill_id = None

    prefill_id, prefill_wf_id, prefill_wf_obj = _resolve_create_prefill_workflow(
        request, prefill_id
    )
    prefill_act_id, prefill_act_obj = _resolve_create_prefill_activity(
        request, prefill_id, prefill_wf_id
    )

    if request.method == "POST":
        try:
            playbook_id = int(request.POST.get("playbook", "0"))
            title = request.POST.get("title", "")
            summary = request.POST.get("summary", "")
            focus_raw = (request.POST.get("focus_workflow") or "").strip()
            focus_wf_id = int(focus_raw) if focus_raw.isdigit() else None
            if focus_wf_id is not None:
                if not Workflow.objects.filter(pk=focus_wf_id, playbook_id=playbook_id).exists():
                    focus_wf_id = None

            focus_act_raw = (request.POST.get("focus_activity") or "").strip()
            focus_act_id = int(focus_act_raw) if focus_act_raw.isdigit() else None
            if focus_act_id is not None:
                q = Activity.objects.filter(pk=focus_act_id, workflow__playbook_id=playbook_id)
                if not q.exists():
                    focus_act_id = None
                elif focus_wf_id is not None and not q.filter(workflow_id=focus_wf_id).exists():
                    focus_act_id = None

            pip = PIPService.create_draft_for_playbook(
                actor=request.user,
                playbook_id=playbook_id,
                title=title,
                summary=summary,
            )
            messages.success(request, f"Saved draft {pip}.")
            url = reverse("pip_edit", kwargs={"pk": pip.pk}) + _pip_edit_suffix_from_focus(
                focus_wf_id, focus_act_id
            )
            return redirect(url)
        except (TypeError, ValueError) as exc:
            messages.error(request, f"Invalid playbook id: {exc}")
        except ValidationError as exc:
            messages.error(request, _format_validation_error(exc))

    return render(
        request,
        "pips/create.html",
        {
            "released_playbooks": released,
            "prefill_playbook_id": prefill_id,
            "prefill_workflow_id": prefill_wf_id,
            "prefill_workflow": prefill_wf_obj,
            "prefill_activity_id": prefill_act_id,
            "prefill_activity": prefill_act_obj,
        },
    )


def _gather_targets(pip):
    from methodology.models import Workflow

    wf_bundle = []
    for wf in Workflow.objects.filter(playbook=pip.playbook).order_by(
        "order", "created_at"
    ):
        acts = list(wf.activities.order_by("order", "pk"))
        wf_bundle.append({"workflow": wf, "activities": acts})
    return {
        "workflow_bundle": wf_bundle,
        "preview_url": reverse("pip_preview", kwargs={"pk": pip.pk}),
    }


@login_required
def pip_draft_editor(request, pk: int):
    from methodology.services.pip_service import PIPService

    pip = PIPService.get_pip(pk, request.user)
    if pip.status != PipModel.STATUS_DRAFT:
        messages.info(request, "PIP is not editable in this state.")
        return redirect("pip_detail", pk=pip.pk)

    focus_wf, focus_act = _validated_pip_focus_ids(pip, request)
    pip_edit_suffix = _pip_edit_suffix_from_focus(focus_wf, focus_act)

    if request.method == "POST":
        if request.POST.get("action") == "save_header":
            try:
                PIPService.save_draft_header(
                    actor=request.user,
                    pip=pip,
                    title=request.POST.get("title", ""),
                    summary=request.POST.get("summary", ""),
                )
                messages.success(request, "Draft header saved.")
            except ValidationError as exc:
                messages.error(request, _format_validation_error(exc))
        return redirect(reverse("pip_edit", kwargs={"pk": pip.pk}) + pip_edit_suffix)

    return render(
        request,
        "pips/draft_editor.html",
        {
            "pip": pip,
            "pip_edit_query_suffix": pip_edit_suffix,
            "prefill_parent_workflow_id": focus_wf,
            "pip_focus_activity_id": focus_act,
            **_gather_targets(pip),
        },
    )


def _parse_optional_int(raw: str) -> int | None:
    val = (raw or "").strip()
    return int(val) if val.isdigit() else None


def _parse_workflow_parent(post) -> tuple[int | None, str]:
    ref_raw = (post.get("parent_workflow_ref") or "").strip()
    wf_raw = (post.get("parent_workflow") or "").strip()
    if ref_raw:
        return None, ref_raw
    if wf_raw.startswith("#"):
        return None, wf_raw
    return _parse_optional_int(wf_raw), ""


def _parse_insert_after(post) -> tuple[int | None, str]:
    ref_raw = (post.get("insert_after_activity_ref") or "").strip()
    ins_raw = (post.get("insert_after_activity") or "").strip()
    if ref_raw:
        return None, ref_raw
    if ins_raw.startswith("#"):
        return None, ins_raw
    return _parse_optional_int(ins_raw), ""


@login_required
@require_POST
def pip_add_change(request, pk: int):
    from methodology.services.pip_service import PIPService

    pip = PIPService.get_pip(pk, request.user)
    post = request.POST
    try:
        parent_wf_id, parent_wf_ref = _parse_workflow_parent(post)
        insert_id, insert_ref = _parse_insert_after(post)
        tgt_raw = post.get("target_id") or ""
        PIPService.add_change(
            actor=request.user,
            pip=pip,
            change_type=(post.get("change_type") or "").strip(),
            entity_type=(post.get("entity_type") or "").strip(),
            name=post.get("name", ""),
            content=post.get("content", ""),
            target_id=int(tgt_raw) if tgt_raw.isdigit() else None,
            parent_workflow_id=parent_wf_id,
            parent_workflow_ref=parent_wf_ref,
            insert_after_activity_id=insert_id,
            insert_after_activity_ref=insert_ref,
            phase_ref=(post.get("phase_ref") or "").strip(),
            produced_by_activity_ref=(post.get("produced_by_activity_ref") or "").strip(),
            artifact_type=(post.get("artifact_type") or "").strip(),
            artifact_is_required=post.get("artifact_is_required") == "on",
            append_to_playbook_end=post.get("append_end") == "on",
            internal_ref=post.get("internal_ref", ""),
            relationship_type=(post.get("relationship_type") or "").strip(),
            source_entity_ref=(post.get("source_entity_ref") or "").strip(),
            target_entity_ref=(post.get("target_entity_ref") or "").strip(),
        )
        messages.success(request, "Change added.")
    except ValidationError as exc:
        messages.error(request, _format_validation_error(exc))
    return redirect(reverse("pip_edit", kwargs={"pk": pip.pk}) + _pip_edit_query_suffix(request))


@login_required
@require_POST
def pip_remove_change(request, pk: int, change_id: int):
    from methodology.services.pip_service import PIPService

    pip = PIPService.get_pip(pk, request.user)
    try:
        PIPService.remove_change(actor=request.user, pip=pip, change_id=change_id)
        messages.success(request, "Change removed.")
    except ValidationError as exc:
        messages.error(request, _format_validation_error(exc))
    return redirect(reverse("pip_edit", kwargs={"pk": pip.pk}) + _pip_edit_query_suffix(request))


@login_required
def pip_preview(request, pk: int):
    from methodology.services.pip_service import PIPService

    pip = PIPService.get_pip(pk, request.user)
    rows = PIPService.summarize_preview_rows(pip)
    return render(request, "pips/preview.html", {"pip": pip, "rows": rows})


@login_required
@require_POST
def pip_submit_review(request, pk: int):
    from methodology.services.pip_service import PIPService

    pip = PIPService.get_pip(pk, request.user)
    try:
        PIPService.submit_for_review(actor=request.user, pip=pip)
        messages.success(request, "PIP submitted — Galdr is reviewing your changes.")
    except ValidationError as exc:
        messages.error(request, _format_validation_error(exc))
        return redirect(reverse("pip_edit", kwargs={"pk": pip.pk}) + _pip_edit_query_suffix(request))
    return redirect("pip_detail", pk=pip.pk)


@login_required
@require_POST
def pip_withdraw(request, pk: int):
    from methodology.services.pip_service import PIPService

    pip = PIPService.get_pip(pk, request.user)
    try:
        PIPService.withdraw_pip(pip, request.user)
        messages.success(request, "PIP withdrawn.")
    except ValidationError as exc:
        messages.error(request, _format_validation_error(exc))
    return redirect("pip_list")


@login_required
def pip_admin_review(request, pk: int):
    """
    Staff-only PIP review page showing Galdr recommendations and editable admin decisions.

    GET: render review form with per-change Galdr output + decision dropdowns.
    POST action=save_decisions: persist admin_decision + admin_note for each change.
    POST action=finalize: save decisions then call PIPAdminService.finalize_pip.
    """
    from django.core.exceptions import PermissionDenied

    from methodology.services.pip_admin_service import PIPAdminService
    from methodology.services.pip_service import PIPService

    if not request.user.is_staff:
        logger.warning(
            f"Non-staff user {request.user.pk} attempted to access admin review for PIP {pk}"
        )
        raise PermissionDenied("Only staff users can review PIPs.")

    pip = PIPService.get_pip_with_changes(pk, request.user)
    changes = list(pip.changes.order_by("order"))

    is_decided = pip.status in (
        PipModel.STATUS_ACCEPTED,
        PipModel.STATUS_ACCEPTED_PARTIAL,
        PipModel.STATUS_REJECTED,
    )

    if request.method == "POST":
        action = request.POST.get("action", "")

        if is_decided:
            messages.error(request, "This PIP has already been decided and cannot be modified.")
            return redirect("pip_detail", pk=pip.pk)

        if action == "save_decisions":
            for change in changes:
                decision = request.POST.get(f"decision_{change.pk}", "").strip()
                note = request.POST.get(f"note_{change.pk}", "").strip()
                if decision in ("ACCEPT", "REJECT"):
                    change.admin_decision = decision
                    change.admin_note = note
                    change.save(update_fields=["admin_decision", "admin_note"])
            messages.success(request, "Decisions saved.")
            return redirect("pip_admin_review", pk=pip.pk)

        elif action == "finalize":
            for change in changes:
                decision = request.POST.get(f"decision_{change.pk}", "").strip()
                note = request.POST.get(f"note_{change.pk}", "").strip()
                if decision in ("ACCEPT", "REJECT"):
                    change.admin_decision = decision
                    change.admin_note = note
                    change.save(update_fields=["admin_decision", "admin_note"])

            try:
                PIPAdminService.finalize_pip(pip, request.user)
                status_label = (
                    "accepted"
                    if pip.status == PipModel.STATUS_ACCEPTED
                    else "partially accepted"
                    if pip.status == PipModel.STATUS_ACCEPTED_PARTIAL
                    else "rejected"
                )
                messages.success(request, f"PIP {status_label} — changes applied.")
            except ValidationError as exc:
                messages.error(request, _format_validation_error(exc))
                return redirect("pip_admin_review", pk=pip.pk)
            return redirect("pip_detail", pk=pip.pk)

    all_decided = all(ch.admin_decision in ("ACCEPT", "REJECT") for ch in changes)
    can_finalize = all_decided and pip.status == PipModel.STATUS_REVIEWED

    accepted_count = sum(1 for ch in changes if ch.admin_decision == "ACCEPT")
    rejected_count = sum(1 for ch in changes if ch.admin_decision == "REJECT")
    pending_count = len(changes) - accepted_count - rejected_count

    logger.info(
        f"Staff user {request.user.pk} viewing admin review for PIP {pk} "
        f"(status={pip.status}, changes={len(changes)})"
    )

    return render(
        request,
        "pips/admin_review.html",
        {
            "pip": pip,
            "changes": changes,
            "can_finalize": can_finalize,
            "is_decided": is_decided,
            "accepted_count": accepted_count,
            "rejected_count": rejected_count,
            "pending_count": pending_count,
        },
    )

