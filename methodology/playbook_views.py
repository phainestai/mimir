"""
Playbook views for CRUDV operations.

Implements 3-step wizard for playbook creation.
"""

import logging
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from methodology.models import Playbook, Workflow, PlaybookVersion
from methodology.forms import (
    PlaybookBasicInfoForm,
    PlaybookWorkflowForm,
    PlaybookPublishingForm
)

logger = logging.getLogger(__name__)


# ==================== LIST ====================

@login_required
def playbook_list(request):
    """List all playbooks for current user."""
    logger.info(f"User {request.user.username} accessing playbook list")
    
    playbooks = Playbook.objects.filter(author=request.user).order_by('-updated_at')
    
    context = {
        'playbooks': playbooks,
        'total_count': playbooks.count()
    }
    
    return render(request, 'playbooks/list.html', context)


# ==================== CREATE WIZARD ====================

def _check_duplicate_playbook(user, name):
    """Check if playbook name already exists for user."""
    return Playbook.objects.filter(author=user, name=name).exists()


def _save_step1_to_session(request, form_data):
    """Save Step 1 form data to session."""
    wizard_data = {
        'name': form_data['name'],
        'description': form_data['description'],
        'category': form_data['category'],
        'tags': form_data['tags'],
        'visibility': form_data.get('visibility', 'private'),
    }
    request.session['wizard_data'] = wizard_data
    logger.info(f"Step 1 data saved to session for user {request.user.username}")


def _save_workflow_to_session(request, workflow_name, workflow_description):
    """Save workflow data to wizard session."""
    wizard_data = request.session['wizard_data']
    wizard_data['workflows'] = [{
        'name': workflow_name,
        'description': workflow_description
    }]
    request.session['wizard_data'] = wizard_data
    logger.info(f"Workflow '{workflow_name}' added to wizard data for user {request.user.username}")


@login_required
def playbook_create(request):
    """
    CREATE Wizard - Step 1: Basic Information.
    
    Collects name, description, category, tags, and visibility.
    Stores in session and proceeds to Step 2.
    
    Template Context:
        - form: PlaybookBasicInfoForm instance
        - step: Current wizard step number (1)
        - step_title: Title for current step
    """
    logger.info(f"User {request.user.username} starting playbook creation wizard - Step 1")
    
    if request.method == 'POST':
        form = PlaybookBasicInfoForm(request.POST)
        
        if form.is_valid():
            logger.info(f"Step 1 form valid for user {request.user.username}")
            name = form.cleaned_data['name']
            
            if _check_duplicate_playbook(request.user, name):
                logger.warning(f"Duplicate playbook name '{name}' for user {request.user.username}")
                form.add_error('name', 'A playbook with this name already exists. Please choose a different name.')
            else:
                _save_step1_to_session(request, form.cleaned_data)
                return redirect('playbook_create_step2')
        else:
            logger.warning(f"Step 1 form invalid for user {request.user.username}: {form.errors}")
    else:
        form = PlaybookBasicInfoForm()
    
    context = {
        'form': form,
        'step': 1,
        'step_title': 'Basic Information'
    }
    
    return render(request, 'playbooks/create_wizard_step1.html', context)


@login_required
def playbook_create_step2(request):
    """
    CREATE Wizard - Step 2: Add Workflows.
    
    Optionally add first workflow or skip to Step 3.
    
    Template Context:
        - form: PlaybookWorkflowForm instance
        - step: Current wizard step number (2)
        - step_title: Title for current step
        - wizard_data: Session data from Step 1
    """
    logger.info(f"User {request.user.username} on playbook creation wizard - Step 2")
    
    if 'wizard_data' not in request.session:
        logger.warning(f"User {request.user.username} tried to access Step 2 without completing Step 1")
        messages.warning(request, 'Please complete Step 1 first.')
        return redirect('playbook_create')
    
    if request.method == 'POST':
        if request.POST.get('skip') == 'true':
            logger.info(f"User {request.user.username} skipping workflow addition")
            return redirect('playbook_create_step3')
        
        form = PlaybookWorkflowForm(request.POST)
        if form.is_valid():
            workflow_name = form.cleaned_data.get('workflow_name', '').strip()
            if workflow_name:
                _save_workflow_to_session(request, workflow_name, form.cleaned_data.get('workflow_description', ''))
            return redirect('playbook_create_step3')
        else:
            logger.warning(f"Step 2 form invalid for user {request.user.username}: {form.errors}")
    else:
        form = PlaybookWorkflowForm()
    
    context = {
        'form': form,
        'step': 2,
        'step_title': 'Add Workflows',
        'wizard_data': request.session.get('wizard_data', {})
    }
    
    return render(request, 'playbooks/create_wizard_step2.html', context)


def _create_playbook_from_wizard(wizard_data, status, user):
    """Create Playbook instance from wizard data."""
    playbook = Playbook.objects.create(
        name=wizard_data['name'],
        description=wizard_data['description'],
        category=wizard_data['category'],
        tags=wizard_data.get('tags', []),
        visibility=wizard_data.get('visibility', 'private'),
        status=status,
        version=1,
        source='owned',
        author=user
    )
    logger.info(f"Playbook '{playbook.name}' (ID: {playbook.pk}) created by {user.username}")
    return playbook


def _create_workflows_for_playbook(wizard_data, playbook):
    """Create Workflow instances for playbook."""
    workflows = wizard_data.get('workflows', [])
    for workflow_data in workflows:
        workflow = Workflow.objects.create(
            name=workflow_data['name'],
            description=workflow_data.get('description', ''),
            playbook=playbook
        )
        logger.info(f"Workflow '{workflow.name}' created for playbook {playbook.pk}")


def _create_initial_version(playbook, user):
    """Create initial version for playbook."""
    snapshot_data = {
        'name': playbook.name,
        'description': playbook.description,
        'category': playbook.category,
        'tags': playbook.tags,
        'visibility': playbook.visibility,
        'status': playbook.status
    }
    
    PlaybookVersion.objects.create(
        playbook=playbook,
        version_number=1,
        snapshot_data=snapshot_data,
        change_summary='Initial version',
        created_by=user
    )
    logger.info(f"Version 1 created for playbook {playbook.pk}")


@login_required
@transaction.atomic
def playbook_create_step3(request):
    """
    CREATE Wizard - Step 3: Publishing.
    
    Review and publish playbook as Draft or Active.
    Creates Playbook, Workflows, and initial PlaybookVersion.
    
    Template Context:
        - form: PlaybookPublishingForm instance
        - step: Current wizard step number (3)
        - step_title: Title for current step
        - wizard_data: Complete wizard session data
    """
    logger.info(f"User {request.user.username} on playbook creation wizard - Step 3")
    
    if 'wizard_data' not in request.session:
        logger.warning(f"User {request.user.username} tried to access Step 3 without completing previous steps")
        messages.warning(request, 'Please complete previous steps first.')
        return redirect('playbook_create')
    
    wizard_data = request.session['wizard_data']
    
    if request.method == 'POST':
        form = PlaybookPublishingForm(request.POST)
        
        if form.is_valid():
            status = form.cleaned_data['status']
            logger.info(f"User {request.user.username} publishing playbook with status: {status}")
            
            try:
                playbook = _create_playbook_from_wizard(wizard_data, status, request.user)
                _create_workflows_for_playbook(wizard_data, playbook)
                _create_initial_version(playbook, request.user)
                
                del request.session['wizard_data']
                messages.success(request, f"Playbook '{playbook.name}' created successfully!")
                return redirect('playbook_detail', pk=playbook.pk)
                
            except Exception as e:
                logger.error(f"Error creating playbook for user {request.user.username}: {str(e)}", exc_info=True)
                messages.error(request, 'An error occurred while creating the playbook. Please try again.')
        else:
            logger.warning(f"Step 3 form invalid for user {request.user.username}: {form.errors}")
    else:
        form = PlaybookPublishingForm()
    
    context = {
        'form': form,
        'step': 3,
        'step_title': 'Publishing',
        'wizard_data': wizard_data
    }
    
    return render(request, 'playbooks/create_wizard_step3.html', context)


# ==================== DETAIL ====================

@login_required
def playbook_detail(request, pk):
    """
    View playbook details.
    
    Template Context:
        - playbook: Playbook instance
        - workflows: QuerySet of related Workflow instances
        - versions: QuerySet of latest 5 PlaybookVersion instances
        - can_edit: Boolean indicating if user can edit playbook
    """
    logger.info(f"User {request.user.username} viewing playbook {pk}")
    
    playbook = get_object_or_404(Playbook, pk=pk)
    
    # Check if user has access
    if playbook.source == 'owned' and playbook.author != request.user:
        logger.warning(f"User {request.user.username} attempted to access playbook {pk} they don't own")
        messages.error(request, "You don't have permission to view this playbook.")
        return redirect('playbook_list')
    
    context = {
        'playbook': playbook,
        'workflows': playbook.workflows.all(),
        'versions': playbook.versions.all()[:5],  # Latest 5 versions
        'can_edit': playbook.can_edit(request.user),
        'quick_stats': playbook.get_quick_stats()
    }
    
    return render(request, 'playbooks/detail.html', context)


# ==================== LEGACY STUBS ====================

@login_required
def playbook_add(request):
    """Legacy add view - redirects to wizard."""
    return redirect('playbook_create')


@login_required
def playbook_edit(request, pk):
    """Edit playbook (stub - to be implemented in EDIT phase)."""
    playbook = get_object_or_404(Playbook, pk=pk)
    messages.info(request, 'Edit functionality coming soon.')
    return redirect('playbook_detail', pk=pk)

# ==================== ACTIONS ====================

@login_required
def playbook_export(request, pk):
    """
    Export playbook to JSON file.
    
    Downloads playbook metadata as JSON.
    Shallow export - metadata only, no workflows/activities yet.
    
    :param request: HTTP request
    :param pk: Playbook primary key
    :returns: JSON file download response
    """
    import json
    from django.http import JsonResponse
    
    logger.info(f"User {request.user.username} exporting playbook {pk}")
    
    playbook = get_object_or_404(Playbook, pk=pk)
    
    # Only owner can export
    if not playbook.is_owned_by(request.user):
        logger.warning(f"User {request.user.username} attempted to export playbook {pk} they don't own")
        messages.error(request, "You can only export playbooks you own.")
        return redirect('playbook_detail', pk=pk)
    
    # Build JSON data
    data = {
        'name': playbook.name,
        'description': playbook.description,
        'category': playbook.category,
        'tags': playbook.tags,
        'visibility': playbook.visibility,
        'status': playbook.status,
        'version': playbook.version,
        'created_at': playbook.created_at.isoformat(),
        'updated_at': playbook.updated_at.isoformat(),
        'note': 'Shallow export - metadata only'
    }
    
    # Create filename
    safe_name = playbook.name.lower().replace(' ', '-').replace('_', '-')
    filename = f"{safe_name}-v{playbook.version}.json"
    
    response = JsonResponse(data)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    logger.info(f"Exported playbook {pk} as {filename}")
    return response


@login_required
def playbook_duplicate(request, pk):
    """
    Duplicate playbook (shallow copy).
    
    Creates new playbook with same metadata but marked as owned.
    Shallow copy - metadata only, no workflows/activities copied yet.
    
    :param request: HTTP request
    :param pk: Playbook primary key to duplicate
    :returns: Redirect to new playbook detail page
    """
    logger.info(f"User {request.user.username} duplicating playbook {pk}")
    
    original = get_object_or_404(Playbook, pk=pk)
    
    if request.method == 'POST':
        new_name = request.POST.get('new_name', f"{original.name} (Copy)")
        
        # Create duplicate
        duplicate = Playbook.objects.create(
            name=new_name,
            description=original.description,
            category=original.category,
            tags=original.tags.copy() if original.tags else [],
            visibility='private',  # Duplicates are always private
            status='draft',  # Duplicates start as draft
            version=1,  # New version sequence
            source='owned',  # Duplicates are always owned
            author=request.user
        )
        
        logger.info(f"Created duplicate playbook {duplicate.pk} from {pk}")
        messages.success(request, f'Playbook duplicated as "{new_name}"')
        return redirect('playbook_detail', pk=duplicate.pk)
    
    # GET request - show form (for now, just redirect with default name)
    return redirect('playbook_detail', pk=pk)


@login_required
def playbook_toggle_status(request, pk):
    """
    Toggle playbook status between active and disabled.
    
    Draft status stays as draft.
    Active <-> Disabled toggle.
    
    :param request: HTTP request
    :param pk: Playbook primary key
    :returns: Redirect to playbook detail page
    """
    logger.info(f"User {request.user.username} toggling status for playbook {pk}")
    
    playbook = get_object_or_404(Playbook, pk=pk)
    
    # Only owner can toggle status
    if not playbook.is_owned_by(request.user):
        logger.warning(f"User {request.user.username} attempted to toggle status on playbook {pk} they don't own")
        messages.error(request, "You can only modify playbooks you own.")
        return redirect('playbook_detail', pk=pk)
    
    if request.method == 'POST':
        # Toggle between active and disabled
        if playbook.status == 'active':
            playbook.status = 'disabled'
            messages.success(request, f'Playbook "{playbook.name}" disabled.')
        elif playbook.status == 'disabled':
            playbook.status = 'active'
            messages.success(request, f'Playbook "{playbook.name}" activated.')
        else:
            # Draft stays draft
            messages.info(request, 'Draft playbooks cannot be toggled. Publish first.')
            return redirect('playbook_detail', pk=pk)
        
        playbook.save()
        logger.info(f"Toggled playbook {pk} status to {playbook.status}")
    
    return redirect('playbook_detail', pk=pk)


@login_required
@transaction.atomic
def playbook_delete(request, pk):
    """
    Delete playbook with confirmation modal and cascade deletion.
    
    Handles:
    - Ownership validation (403 if not owner)
    - Cascade deletion of workflows, activities, artifacts, etc.
    - Success notification with playbook name
    - Redirect to playbook list
    
    :param request: HTTP request
    :param pk: Playbook primary key
    :returns: Redirect to playbook list or 403
    :raises: Http404 if playbook not found
    
    Examples:
        - POST /playbooks/123/delete/ → deletes playbook 123
        - Returns 403 if user doesn't own playbook
    """
    logger.info(f"User {request.user.username} attempting to delete playbook {pk}")
    
    playbook = get_object_or_404(Playbook, pk=pk)
    
    # Only owner can delete
    if not playbook.is_owned_by(request.user):
        logger.warning(f"User {request.user.username} attempted to delete playbook {pk} they don't own")
        messages.error(request, "You can only delete playbooks you own.")
        return redirect('playbook_list')
    
    if request.method == 'POST':
        playbook_name = playbook.name
        
        # Get dependency counts for logging
        workflow_count = playbook.workflows.count()
        
        logger.info(
            f"Deleting playbook {pk} '{playbook_name}' with {workflow_count} workflows "
            f"for user {request.user.username}"
        )
        
        # CASCADE DELETE: Django will automatically delete related:
        # - Workflows (via foreign key with on_delete=CASCADE)
        # - Activities (via workflow cascade)
        # - Playbook versions
        # - Artifacts
        # - Roles
        # - Howtos
        playbook.delete()
        
        logger.info(f"Successfully deleted playbook '{playbook_name}' (id={pk})")
        messages.success(request, f"Playbook '{playbook_name}' deleted successfully.")
        
        return redirect('playbook_list')
    
    # If GET request, render confirmation modal (handled in template)
    return redirect('playbook_detail', pk=pk)
