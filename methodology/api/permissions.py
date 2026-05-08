"""
DRF Permissions for Mimir API.

Enforces ownership and draft/released status rules.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    
    For Phase 4: Will be extended to check group membership for shared playbooks.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user owns the object or has read-only access.
        
        :param request: HTTP request
        :param view: DRF view
        :param obj: Model instance being accessed
        :return: True if permission granted, False otherwise
        """
        # Read permissions are allowed to any authenticated user
        # (Phase 4 will add group-based filtering)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for owner
        # Handle different model types
        if hasattr(obj, 'author'):
            # Playbook model
            return obj.author == request.user
        elif hasattr(obj, 'playbook'):
            # Workflow, Activity, Skill, Agent, Artifact, Phase, Rule
            return obj.playbook.author == request.user
        elif hasattr(obj, 'workflow'):
            # Activity model (via workflow)
            return obj.workflow.playbook.author == request.user
        
        # Default deny
        return False


class IsDraftPlaybook(permissions.BasePermission):
    """
    Permission to only allow modifications to draft playbooks.
    
    Released playbooks require PIP workflow.
    """
    
    message = 'Cannot modify released playbook. Use create_pip instead.'
    
    def has_object_permission(self, request, view, obj):
        """
        Check if playbook is in draft status.
        
        :param request: HTTP request
        :param view: DRF view
        :param obj: Model instance being accessed
        :return: True if draft or read-only, False if released and write operation
        """
        # Read operations always allowed
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write operations only allowed on draft playbooks
        # Handle different model types
        if hasattr(obj, 'status'):
            # Playbook model
            return obj.status == 'draft'
        elif hasattr(obj, 'playbook'):
            # Workflow, Skill, Agent, Artifact, Phase, Rule
            return obj.playbook.status == 'draft'
        elif hasattr(obj, 'workflow'):
            # Activity model (via workflow)
            return obj.workflow.playbook.status == 'draft'
        
        # Default allow (for create operations)
        return True
