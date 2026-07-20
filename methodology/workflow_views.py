"""Workflow views for CRUDV operations."""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError

from methodology.models import Playbook, Workflow
from methodology.services.workflow_service import WorkflowService
from methodology.services.activity_service import ActivityService
from methodology.utils.playbook_access import playbook_readable_or_404

logger = logging.getLogger(__name__)

# ─── NO ORM IN VIEWS ────────────────────────────────────────────────────────
# Views are thin controllers. NEVER query the ORM directly here.
# All data access must go through services in methodology/services/.
# Both views and MCP tools drink from the same service well.
# ────────────────────────────────────────────────────────────────────────────


@login_required
def workflow_global_list(request):
    """
    Global workflows overview - all workflows across all playbooks.
    
    Shows workflows from all playbooks accessible to the user (owned + public + team).
    Useful for seeing workflow patterns and managing across playbooks.
    """
    # Get all workflows via service
    workflows = WorkflowService.list_global_workflows(request.user)
    
    # Count unique playbooks
    playbook_count = workflows.values('playbook').distinct().count()

    # Sum activities across all returned workflows
    total_activity_count = sum(w.get_activity_count() for w in workflows)

    logger.info(
        f"User {request.user.username} viewing global workflows list "
        f"({workflows.count()} workflows, {total_activity_count} activities)"
    )

    return render(request, 'workflows/global_list.html', {
        'workflows': workflows,
        'playbook_count': playbook_count,
        'total_activity_count': total_activity_count,
    })


@login_required
def workflow_create(request, playbook_pk):
    """
    Create new workflow in playbook.
    
    GET: Show creation form
    POST: Create workflow and redirect to detail
    """
    playbook = get_object_or_404(Playbook, pk=playbook_pk)
    
    # Only owner can create workflows
    if not playbook.can_edit(request.user):
        messages.error(request, "You can only create workflows in playbooks you own.")
        return redirect('playbook_detail', pk=playbook_pk)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        # Validate name
        if not name:
            messages.error(request, "Name is required")
            return render(request, 'workflows/create.html', {
                'playbook': playbook,
                'name': name,
                'description': description
            })
        
        try:
            workflow = WorkflowService.create_workflow(
                playbook=playbook,
                name=name,
                description=description
            )
            
            logger.info(f"User {request.user.username} created workflow {workflow.pk}")
            messages.success(request, f"Workflow '{workflow.name}' created in {playbook.name}")
            return redirect('workflow_detail', playbook_pk=playbook.pk, pk=workflow.pk)
            
        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, 'workflows/create.html', {
                'playbook': playbook,
                'name': name,
                'description': description
            })
    
    # GET request
    return render(request, 'workflows/create.html', {
        'playbook': playbook
    })


@login_required
def workflow_detail(request, playbook_pk, pk):
    """
    View workflow details with activities flow diagram.
    
    Displays workflow information and generates Graphviz SVG visualization
    of activities in sequential flow with phase grouping if applicable.
    
    Template: workflows/detail.html
    Context:
        - playbook: Playbook instance
        - workflow: Workflow instance
        - can_edit: Boolean, True if user can edit workflow
        - activities_svg: SVG string from Graphviz or None if no activities
        - activity_count: Integer count of activities in workflow
        - has_activities: Boolean, True if activity_count > 0
    
    :param request: Django HTTP request
    :param playbook_pk: Playbook primary key
    :param pk: Workflow primary key
    :return: Rendered template response
    """
    playbook = playbook_readable_or_404(request, playbook_pk)
    workflow = get_object_or_404(Workflow, pk=pk, playbook=playbook)

    # Fetch activities and generate graph
    from methodology.services.activity_graph_service import ActivityGraphService

    activities = ActivityService.get_activities_for_workflow(workflow)
    activity_count = activities.count()
    
    # Generate SVG graph if activities exist
    activities_svg = None
    if activity_count > 0:
        try:
            graph_service = ActivityGraphService()
            activities_svg = graph_service.generate_activities_graph(workflow, playbook)
            logger.info(f"Generated activity graph for workflow {pk} with {activity_count} activities")
        except Exception as e:
            logger.error(f"Failed to generate activity graph for workflow {pk}: {str(e)}")
            # Continue without graph - template will show error or plain list
    
    can_submit_pip = (
        playbook.source == "owned"
        and playbook.author_id == request.user.id
        and playbook.is_released
    )
    logger.info(
        "User %s viewing workflow pk=%s playbook=%s can_edit=%s can_submit_pip=%s",
        request.user.username,
        pk,
        playbook_pk,
        workflow.can_edit(request.user),
        can_submit_pip,
    )

    context = {
        'playbook': playbook,
        'workflow': workflow,
        'can_edit': workflow.can_edit(request.user),
        'can_submit_pip': can_submit_pip,
        'activities_svg': activities_svg,
        'activity_count': activity_count,
        'has_activities': activity_count > 0,
        'activities': activities,
    }
    if request.GET.get('embed') == '1':
        return render(request, 'workflows/_embed.html', context)
    return render(request, 'workflows/detail.html', context)


@login_required
def workflow_list(request, playbook_pk):
    """List workflows for playbook."""
    playbook = playbook_readable_or_404(request, playbook_pk)
    workflows = WorkflowService.get_workflows_for_playbook(playbook_pk)

    return render(request, 'workflows/list.html', {
        'playbook': playbook,
        'workflows': workflows,
        'can_edit': playbook.can_edit(request.user)
    })


@login_required
def workflow_edit(request, playbook_pk, pk):
    """Edit workflow."""
    playbook = get_object_or_404(Playbook, pk=playbook_pk)
    workflow = get_object_or_404(Workflow, pk=pk, playbook=playbook)
    
    # Only owner can edit
    if not workflow.can_edit(request.user):
        messages.error(request, "You can only edit workflows in playbooks you own.")
        return redirect('workflow_detail', playbook_pk=playbook_pk, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        order = request.POST.get('order', workflow.order)
        
        if not name:
            messages.error(request, "Name is required")
            return render(request, 'workflows/edit.html', {
                'playbook': playbook,
                'workflow': workflow,
                'name': name,
                'description': description
            })
        
        try:
            updated = WorkflowService.update_workflow(
                workflow_id=workflow.pk,
                name=name,
                description=description,
                order=int(order)
            )
            
            logger.info(f"User {request.user.username} updated workflow {workflow.pk}")
            messages.success(request, f"Workflow '{updated.name}' updated successfully")
            return redirect('workflow_detail', playbook_pk=playbook.pk, pk=updated.pk)
            
        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, 'workflows/edit.html', {
                'playbook': playbook,
                'workflow': workflow,
                'name': name,
                'description': description
            })
    
    # GET request
    return render(request, 'workflows/edit.html', {
        'playbook': playbook,
        'workflow': workflow
    })


@login_required
def workflow_delete(request, playbook_pk, pk):
    """Delete workflow."""
    playbook = get_object_or_404(Playbook, pk=playbook_pk)
    workflow = get_object_or_404(Workflow, pk=pk, playbook=playbook)
    
    # Only owner can delete
    if not workflow.can_edit(request.user):
        messages.error(request, "You can only delete workflows in playbooks you own.")
        return redirect('workflow_detail', playbook_pk=playbook_pk, pk=pk)
    
    if request.method == 'POST':
        workflow_name = workflow.name
        
        try:
            WorkflowService.delete_workflow(workflow.pk)
            logger.info(f"User {request.user.username} deleted workflow {pk}")
            messages.success(request, f"Workflow '{workflow_name}' deleted successfully")
            return redirect('workflow_list', playbook_pk=playbook.pk)
            
        except Exception as e:
            logger.error(f"Error deleting workflow {pk}: {e}")
            messages.error(request, "Error deleting workflow")
            return redirect('workflow_detail', playbook_pk=playbook_pk, pk=pk)
    
    # GET request - show confirmation (or redirect to detail)
    return redirect('workflow_detail', playbook_pk=playbook_pk, pk=pk)


@login_required
def workflow_duplicate(request, playbook_pk, pk):
    """Duplicate workflow."""
    playbook = get_object_or_404(Playbook, pk=playbook_pk)
    workflow = get_object_or_404(Workflow, pk=pk, playbook=playbook)
    
    # Only owner can duplicate
    if not workflow.can_edit(request.user):
        messages.error(request, "You can only duplicate workflows in playbooks you own.")
        return redirect('workflow_detail', playbook_pk=playbook_pk, pk=pk)
    
    if request.method == 'POST':
        new_name = request.POST.get('new_name', f"{workflow.name} (Copy)").strip()
        
        try:
            duplicate = WorkflowService.duplicate_workflow(
                workflow_id=workflow.pk,
                new_name=new_name
            )
            
            logger.info(f"User {request.user.username} duplicated workflow {pk} as {duplicate.pk}")
            messages.success(request, f"Workflow duplicated as '{duplicate.name}'")
            return redirect('workflow_detail', playbook_pk=playbook.pk, pk=duplicate.pk)
            
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('workflow_detail', playbook_pk=playbook_pk, pk=pk)
    
    # GET request - redirect to detail
    return redirect('workflow_detail', playbook_pk=playbook_pk, pk=pk)
