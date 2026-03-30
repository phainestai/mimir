"""
Skill views for CRUDV operations.

Provides views for listing, creating, viewing, editing, and deleting skills
attached to activities.
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError

from methodology.models import Playbook, Workflow, Activity
from methodology.services.skill_service import SkillService

logger = logging.getLogger(__name__)


# ==================== GLOBAL LIST ====================

@login_required
def skill_list_global(request):
    """
    Global skills list — all skills across all playbooks owned by the user.

    Supports search via ?q= query parameter.

    Template: skills/list.html
    Template Context:
        - skills: QuerySet of Skill instances
        - query: Current search string
        - total_count: Total skills before filtering

    :param request: Django request object
    :return: Rendered global list template
    """
    query = request.GET.get('q', '').strip()
    skills = SkillService.search_skills(query=query, user=request.user)
    total_count = SkillService.search_skills(query='', user=request.user).count()

    logger.info(
        f"User {request.user.username} viewing global skill list"
        f"{f', query={query!r}' if query else ''}"
    )

    context = {
        'skills': skills,
        'query': query,
        'total_count': total_count,
    }
    return render(request, 'skills/list.html', context)


# ==================== ACTIVITY-SCOPED VIEWS ====================

def _get_activity_or_redirect(request, playbook_pk, workflow_pk, activity_pk):
    """
    Retrieve playbook, workflow, and activity with permission check.

    :returns: (playbook, workflow, activity) tuple, or None if permission denied
              (in which case the caller should return the redirect immediately)
    :rtype: tuple | None
    """
    playbook = get_object_or_404(Playbook, pk=playbook_pk)
    workflow = get_object_or_404(Workflow, pk=workflow_pk, playbook=playbook)
    activity = get_object_or_404(Activity, pk=activity_pk, workflow=workflow)

    if playbook.source == 'owned' and playbook.author != request.user:
        logger.warning(
            f"User {request.user.username} attempted to access activity {activity_pk} "
            f"they don't own"
        )
        messages.error(request, "You don't have permission to access this skill.")
        return None

    return playbook, workflow, activity


@login_required
def skill_detail(request, playbook_pk, workflow_pk, activity_pk):
    """
    Display the skill for an activity (or a create CTA if none exists).

    Template: skills/detail.html
    Template Context:
        - playbook, workflow, activity: Parent objects
        - skill: Skill instance or None
        - can_edit: Boolean

    :param request: Django request object
    :param playbook_pk: Playbook primary key
    :param workflow_pk: Workflow primary key
    :param activity_pk: Activity primary key
    :return: Rendered detail template or redirect
    """
    result = _get_activity_or_redirect(request, playbook_pk, workflow_pk, activity_pk)
    if result is None:
        return redirect('playbook_list')
    playbook, workflow, activity = result

    skill = SkillService.get_skill_for_activity(activity_pk)

    logger.info(
        f"User {request.user.username} viewing skill for activity {activity_pk}"
        f"{'' if skill else ' (no skill yet)'}"
    )

    context = {
        'playbook': playbook,
        'workflow': workflow,
        'activity': activity,
        'skill': skill,
        'can_edit': activity.can_edit(request.user),
    }
    return render(request, 'skills/detail.html', context)


@login_required
def skill_create(request, playbook_pk, workflow_pk, activity_pk):
    """
    Create a new skill for an activity.

    GET: Render empty create form.
    POST: Validate and create skill; redirect to detail on success.

    Template: skills/create.html
    Template Context:
        - playbook, workflow, activity: Parent objects
        - form_data: Submitted POST data (for re-display on error)
        - errors: Dict of field → error message

    :param request: Django request object
    :param playbook_pk: Playbook primary key
    :param workflow_pk: Workflow primary key
    :param activity_pk: Activity primary key
    :return: Rendered form or redirect
    """
    result = _get_activity_or_redirect(request, playbook_pk, workflow_pk, activity_pk)
    if result is None:
        return redirect('playbook_list')
    playbook, workflow, activity = result

    if not activity.can_edit(request.user):
        logger.warning(
            f"User {request.user.username} attempted skill create without edit permission"
        )
        messages.error(request, "You don't have permission to create skills for this activity.")
        return redirect('playbook_list')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()

        try:
            skill = SkillService.create_skill(activity=activity, title=title, content=content)
            messages.success(request, f"Skill '{skill.title}' created successfully!")
            return redirect('skill_detail', playbook_pk=playbook_pk,
                            workflow_pk=workflow_pk, activity_pk=activity_pk)
        except ValidationError as e:
            logger.warning(f"Skill create validation error: {e}")
            return _render_create_form(
                request, playbook, workflow, activity,
                form_data=request.POST,
                errors={'title': str(e.message)}
            )

    return _render_create_form(request, playbook, workflow, activity, {}, {})


@login_required
def skill_edit(request, playbook_pk, workflow_pk, activity_pk):
    """
    Edit an existing skill.

    GET: Render pre-populated edit form.
    POST: Validate and update skill; redirect to detail on success.

    Template: skills/edit.html (reuses create.html layout with pre-populated values)
    Template Context:
        - playbook, workflow, activity, skill: Objects
        - form_data: Current or submitted values
        - errors: Dict of field → error message

    :param request: Django request object
    :param playbook_pk: Playbook primary key
    :param workflow_pk: Workflow primary key
    :param activity_pk: Activity primary key
    :return: Rendered form or redirect
    """
    result = _get_activity_or_redirect(request, playbook_pk, workflow_pk, activity_pk)
    if result is None:
        return redirect('playbook_list')
    playbook, workflow, activity = result

    if not activity.can_edit(request.user):
        messages.error(request, "You don't have permission to edit this skill.")
        return redirect('playbook_list')

    skill = SkillService.get_skill_for_activity(activity_pk)
    if skill is None:
        messages.warning(request, "No skill exists for this activity yet.")
        return redirect('skill_create', playbook_pk=playbook_pk,
                        workflow_pk=workflow_pk, activity_pk=activity_pk)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()

        try:
            skill = SkillService.update_skill(skill.pk, title=title, content=content)
            messages.success(request, f"Skill '{skill.title}' updated successfully!")
            return redirect('skill_detail', playbook_pk=playbook_pk,
                            workflow_pk=workflow_pk, activity_pk=activity_pk)
        except ValidationError as e:
            logger.warning(f"Skill edit validation error: {e}")
            return _render_edit_form(
                request, playbook, workflow, activity, skill,
                form_data=request.POST,
                errors={'title': str(e.message)}
            )

    return _render_edit_form(
        request, playbook, workflow, activity, skill,
        form_data={'title': skill.title, 'content': skill.content},
        errors={}
    )


@login_required
def skill_delete_confirm(request, playbook_pk, workflow_pk, activity_pk):
    """
    Return the delete confirmation modal partial (loaded via HTMX).

    Template: skills/_delete_modal.html

    :param request: Django request object
    :param playbook_pk: Playbook primary key
    :param workflow_pk: Workflow primary key
    :param activity_pk: Activity primary key
    :return: Rendered modal partial
    """
    result = _get_activity_or_redirect(request, playbook_pk, workflow_pk, activity_pk)
    if result is None:
        return redirect('playbook_list')
    playbook, workflow, activity = result

    skill = SkillService.get_skill_for_activity(activity_pk)
    if skill is None:
        return redirect('skill_detail', playbook_pk=playbook_pk,
                        workflow_pk=workflow_pk, activity_pk=activity_pk)

    delete_url = _build_skill_url(playbook_pk, workflow_pk, activity_pk, 'skill_delete')
    context = {
        'playbook': playbook,
        'workflow': workflow,
        'activity': activity,
        'skill': skill,
        'delete_url': delete_url,
    }
    return render(request, 'skills/_delete_modal.html', context)


@login_required
def skill_delete(request, playbook_pk, workflow_pk, activity_pk):
    """
    Delete a skill (POST only).

    :param request: Django request object
    :param playbook_pk: Playbook primary key
    :param workflow_pk: Workflow primary key
    :param activity_pk: Activity primary key
    :return: Redirect to skill list on success
    """
    result = _get_activity_or_redirect(request, playbook_pk, workflow_pk, activity_pk)
    if result is None:
        return redirect('playbook_list')
    playbook, workflow, activity = result

    if not activity.can_edit(request.user):
        messages.error(request, "You don't have permission to delete this skill.")
        return redirect('playbook_list')

    skill = SkillService.get_skill_for_activity(activity_pk)
    if skill is None:
        messages.warning(request, "No skill found for this activity.")
        return redirect('skill_list')

    title = skill.title
    SkillService.delete_skill(skill.pk)
    messages.success(request, f"Skill '{title}' deleted successfully.")
    return redirect('skill_list')


# ==================== PRIVATE HELPERS ====================

def _build_skill_url(playbook_pk, workflow_pk, activity_pk, view_name):
    """Build a skill URL string from kwargs."""
    from django.urls import reverse
    return reverse(view_name, kwargs={
        'playbook_pk': playbook_pk,
        'workflow_pk': workflow_pk,
        'activity_pk': activity_pk,
    })


def _render_create_form(request, playbook, workflow, activity, form_data, errors):
    """
    Render the skill create form template with context.

    :param request: Django request object
    :param playbook: Playbook instance
    :param workflow: Workflow instance
    :param activity: Activity instance
    :param form_data: Dict of current field values
    :param errors: Dict of field → error message
    :return: Rendered create form response
    """
    context = {
        'playbook': playbook,
        'workflow': workflow,
        'activity': activity,
        'form_data': form_data,
        'errors': errors,
    }
    return render(request, 'skills/create.html', context)


def _render_edit_form(request, playbook, workflow, activity, skill, form_data, errors):
    """
    Render the skill edit form template with context.

    :param request: Django request object
    :param playbook: Playbook instance
    :param workflow: Workflow instance
    :param activity: Activity instance
    :param skill: Skill instance
    :param form_data: Dict of current field values
    :param errors: Dict of field → error message
    :return: Rendered edit form response
    """
    context = {
        'playbook': playbook,
        'workflow': workflow,
        'activity': activity,
        'skill': skill,
        'form_data': form_data,
        'errors': errors,
    }
    return render(request, 'skills/edit.html', context)
