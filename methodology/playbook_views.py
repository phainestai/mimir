"""
Playbook views for CRUDV operations.

Provides views for listing, creating, viewing, editing, and deleting playbooks.
Includes a 3-step creation wizard and export/import functionality.
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from methodology.forms.playbook_forms import PlaybookBasicInfoForm
from methodology.models import Playbook, Workflow
from methodology.services.playbook_service import PlaybookService

logger = logging.getLogger(__name__)


# ==================== LIST ====================

@login_required
def playbook_list(request):
    """
    List all playbooks owned by the current user.

    Template: playbooks/list.html
    Context: playbooks — QuerySet of Playbook instances

    :param request: Django request object
    :return: Rendered list template
    """
    playbooks = PlaybookService.list_playbooks(author=request.user)
    logger.info(f"User {request.user.username} viewing playbook list ({len(playbooks)} playbooks)")
    return render(request, 'playbooks/list.html', {'playbooks': playbooks})


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
    if request.method == 'POST':
        form = PlaybookBasicInfoForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data['name']

            # Check for duplicate name (requires user context, not in form)
            if Playbook.objects.filter(author=request.user, name=name).exists():
                form.add_error('name', 'A playbook with this name already exists')
                return render(request, 'playbooks/create_wizard_step1.html', {'form': form})

            wizard_data = {
                'name': name,
                'description': form.cleaned_data['description'],
                'category': form.cleaned_data['category'],
                'visibility': form.cleaned_data.get('visibility', 'private'),
                'tags': form.cleaned_data.get('tags', []),
            }
            request.session['wizard_data'] = wizard_data
            logger.info(f"Playbook wizard step 1 completed by {request.user.username}: '{name}'")
            return redirect('playbook_create_step2')

        return render(request, 'playbooks/create_wizard_step1.html', {'form': form})

    form = PlaybookBasicInfoForm()
    return render(request, 'playbooks/create_wizard_step1.html', {'form': form})


@login_required
def playbook_create_step2(request):
    """
    Step 2 of the creation wizard (optional workflows).

    GET: Render step-2 form.
    POST: Store workflows in session; redirect to step 3.

    :param request: Django request object
    :return: Rendered step-2 form or redirect
    """
    wizard_data = request.session.get('wizard_data')
    if not wizard_data:
        return redirect('playbook_create')

    if request.method == 'POST':
        wizard_data['workflows'] = request.POST.getlist('workflow_names', [])
        request.session['wizard_data'] = wizard_data
        return redirect('playbook_create_step3')

    return render(request, 'playbooks/create_wizard_step2.html', {
        'wizard_data': wizard_data,
    })


@login_required
def playbook_create_step3(request):
    """
    Step 3 (review and submit) of the creation wizard.

    GET: Show review/summary page.
    POST: Create the playbook and redirect to detail.

    :param request: Django request object
    :return: Rendered step-3 form or redirect to detail
    """
    wizard_data = request.session.get('wizard_data')
    if not wizard_data:
        return redirect('playbook_create')

    if request.method == 'POST':
        status = request.POST.get('status', wizard_data.get('status', 'draft'))
        try:
            playbook = PlaybookService.create_playbook(
                name=wizard_data['name'],
                description=wizard_data['description'],
                category=wizard_data['category'],
                author=request.user,
                status=status,
                visibility=wizard_data.get('visibility', 'private'),
            )
            if wizard_data.get('tags'):
                playbook.tags = wizard_data['tags']
                playbook.save()

            del request.session['wizard_data']
            messages.success(request, f"Playbook '{playbook.name}' created successfully!")
            logger.info(f"Playbook '{playbook.name}' (id={playbook.pk}) created by {request.user.username}")
            return redirect('playbook_detail', pk=playbook.pk)

        except ValidationError as e:
            messages.error(request, str(e.message))
            return render(request, 'playbooks/create_wizard_step3.html', {'wizard_data': wizard_data})

    return render(request, 'playbooks/create_wizard_step3.html', {'wizard_data': wizard_data})


# ==================== LEGACY ====================

@login_required
def playbook_add(request):
    """Legacy redirect to new creation wizard."""
    return redirect('playbook_create')


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
    playbook = get_object_or_404(Playbook, pk=pk)
    workflows = Workflow.objects.filter(playbook=playbook).order_by('order', 'created_at')
    quick_stats = playbook.get_quick_stats()
    can_edit = playbook.can_edit(request.user)

    logger.info(f"User {request.user.username} viewing playbook '{playbook.name}' (id={pk})")

    context = {
        'playbook': playbook,
        'workflows': workflows,
        'quick_stats': quick_stats,
        'can_edit': can_edit,
    }
    return render(request, 'playbooks/detail.html', context)


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
        return redirect('playbook_detail', pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', '').strip()
        visibility = request.POST.get('visibility', '').strip()

        if not name:
            return render(request, 'playbooks/edit.html', {
                'playbook': playbook,
                'errors': {'name': 'Name is required'},
                'form_data': request.POST,
            })

        try:
            PlaybookService.update_playbook(
                pk, name=name, description=description,
                category=category, visibility=visibility
            )
            messages.success(request, f"Playbook '{name}' updated successfully!")
            logger.info(f"Playbook {pk} updated by {request.user.username}")
            return redirect('playbook_detail', pk=pk)
        except ValidationError as e:
            return render(request, 'playbooks/edit.html', {
                'playbook': playbook,
                'errors': {'name': str(e.message)},
                'form_data': request.POST,
            })

    return render(request, 'playbooks/edit.html', {
        'playbook': playbook,
        'errors': {},
        'form_data': {},
    })


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
        return redirect('playbook_list')

    return render(request, 'playbooks/delete_modal.html', {'playbook': playbook})


@login_required
def playbook_delete(request, pk):
    """
    Delete a playbook (POST only). GET redirects to detail.

    :param request: Django request object
    :param pk: Playbook primary key
    :return: Redirect to playbook list (on POST) or detail (on GET)
    """
    playbook = get_object_or_404(Playbook, pk=pk)

    if request.method != 'POST':
        return redirect('playbook_detail', pk=pk)

    if not playbook.is_owned_by(request.user):
        messages.error(request, "You don't have permission to delete this playbook.")
        return redirect('playbook_list')

    name = playbook.name
    PlaybookService.delete_playbook(pk)
    messages.success(request, f"Playbook '{name}' deleted successfully.")
    logger.info(f"Playbook '{name}' (id={pk}) deleted by {request.user.username}")
    return redirect('playbook_list')


# ==================== ACTIONS ====================

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
    logger.info(f"User {request.user.username} exporting playbook {pk}")

    data = {
        'id': playbook.pk,
        'name': playbook.name,
        'description': playbook.description,
        'category': playbook.category,
        'version': str(playbook.version),
        'status': playbook.status,
    }
    filename = f"{slugify(playbook.name)}.json"
    response = JsonResponse(data)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
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
    new_name = request.POST.get('new_name', f"Copy of {playbook.name}").strip() or f"Copy of {playbook.name}"

    try:
        duplicate = PlaybookService.duplicate_playbook(pk, new_name, request.user)
        messages.success(request, f"Playbook duplicated as '{duplicate.name}'.")
        return redirect('playbook_detail', pk=duplicate.pk)
    except ValidationError as e:
        messages.error(request, str(e.message))
        return redirect('playbook_detail', pk=pk)


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
        messages.error(request, "You don't have permission to change this playbook's status.")
        return redirect('playbook_detail', pk=pk)

    new_status = 'disabled' if playbook.status == 'active' else 'active'
    PlaybookService.update_playbook(pk, status=new_status)
    messages.success(request, f"Playbook status changed to '{new_status}'.")
    logger.info(f"Playbook {pk} status toggled to {new_status} by {request.user.username}")
    return redirect('playbook_detail', pk=pk)


# ==================== PRIVATE HELPERS (none currently) ====================
