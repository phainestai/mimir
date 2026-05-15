"""
DRF Permissions for Mimir API.

Enforces ownership and draft/released status rules.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    
    Phase 4: Checks group membership for shared playbooks.
    - Read access: Owner OR member of shared group
    - Write access: Owner only
    """
    
    def _user_can_access_playbook(self, user, playbook):
        """
        Check if user can access playbook (owner or group member).
        
        :param user: User instance
        :param playbook: Playbook instance
        :return: True if user has access
        """
        # Owner always has access
        if playbook.author == user:
            return True
        
        # Check if user is in any of the shared groups
        user_groups = set(user.groups.all())
        shared_groups = set(playbook.shared_with_groups.all())
        return bool(user_groups & shared_groups)
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user owns the object or has group-based access.
        
        :param request: HTTP request
        :param view: DRF view
        :param obj: Model instance being accessed
        :return: True if permission granted, False otherwise
        """
        # Get the playbook for this object
        playbook = None
        if hasattr(obj, 'author'):
            # Playbook model
            playbook = obj
        elif hasattr(obj, 'playbook'):
            # Workflow, Skill, Agent, Artifact, Phase, Rule
            playbook = obj.playbook
        elif hasattr(obj, 'workflow'):
            # Activity model (via workflow)
            playbook = obj.workflow.playbook
        
        if not playbook:
            return False
        
        # Read permissions: owner OR group member
        if request.method in permissions.SAFE_METHODS:
            return self._user_can_access_playbook(request.user, playbook)
        
        # Write permissions: owner only
        return playbook.author == request.user


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
