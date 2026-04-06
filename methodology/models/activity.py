"""
Activity model for individual tasks within workflows.

Activities represent discrete work items that make up a workflow.
Each activity belongs to a workflow and can be organized into phases.
"""

from django.db import models


class Activity(models.Model):
    """
    Activity represents a single task/step within a workflow.
    
    Activities are ordered work items that can be grouped by phase,
    tracked by status, and can have dependencies on other activities.
    """
    
    # Relationships
    workflow = models.ForeignKey(
        'Workflow',
        on_delete=models.CASCADE,
        related_name='activities',
        help_text="Parent workflow containing this activity"
    )
    agent = models.ForeignKey(
        'Agent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
        help_text="Optional AI agent assigned to perform this activity"
    )
    skill = models.ForeignKey(
        'Skill',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
        help_text="Optional skill providing tech-specific guidance for this activity"
    )
    
    # Core fields
    name = models.CharField(
        max_length=200,
        help_text="Activity name - must be unique within workflow"
    )
    guidance = models.TextField(
        help_text="Rich Markdown guidance with instructions, examples, images, and diagrams"
    )
    
    # Organization
    order = models.IntegerField(
        default=1,
        help_text="Execution order within workflow"
    )
    phase = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Optional phase grouping (e.g., 'Planning', 'Execution')"
    )
    
    # Dependencies - predecessor/successor relationships
    predecessor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='successors',
        help_text="Previous activity that must complete first"
    )
    successor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='predecessors',
        help_text="Next activity that depends on this one"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when activity was last accessed/viewed (for Recent Activity tracking)"
    )
    
    class Meta:
        ordering = ['workflow', 'order', 'name']
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'
        constraints = [
            models.UniqueConstraint(
                fields=['workflow', 'name'],
                name='unique_activity_per_workflow'
            )
        ]
    
    def __str__(self):
        """String representation showing name and order."""
        return f"{self.name} (#{self.order})"
    
    def is_owned_by(self, user):
        """
        Check if user owns the parent workflow's playbook.
        
        :param user: User to check ownership for
        :returns: True if user owns parent playbook
        :rtype: bool
        
        Example:
            >>> activity.is_owned_by(maria)
            True  # If maria owns the playbook
        """
        return self.workflow.playbook.is_owned_by(user)
    
    def can_edit(self, user):
        """
        Check if user can edit this activity.
        
        User can edit if they own the parent playbook and it's an owned playbook.
        
        :param user: User to check edit permission for
        :returns: True if user can edit
        :rtype: bool
        
        Example:
            >>> activity.can_edit(maria)
            True  # If maria owns the playbook
        """
        return self.workflow.can_edit(user)
    
    def get_phase_display_name(self):
        """
        Get formatted phase name or default.
        
        :returns: Phase name or 'Unassigned' if no phase set
        :rtype: str
        
        Example:
            >>> activity.get_phase_display_name()
            'Planning'  # If phase is set
            >>> no_phase_activity.get_phase_display_name()
            'Unassigned'  # If phase is None or empty
        """
        return self.phase if self.phase else "Unassigned"
    
    @property
    def reference_name(self) -> str:
        """
        Generate reference name from workflow abbreviation and order.
        
        :returns: Reference name (e.g., 'DFS1', 'PLG3')
        :rtype: str
        
        Example:
            >>> activity.workflow.abbreviation = 'DFS'
            >>> activity.order = 1
            >>> activity.reference_name
            'DFS1'
        """
        return f"{self.workflow.abbreviation}{self.order}"
    
    def clean(self):
        """
        Validate activity dependencies.
        
        :raises ValidationError: If validation fails
        
        Validations:
        - Predecessor must be in same workflow
        - Successor must be in same workflow
        - Cannot be self-referential
        - No circular dependencies
        """
        from django.core.exceptions import ValidationError
        
        # Validate predecessor is in same workflow
        if self.predecessor and self.predecessor.workflow_id != self.workflow_id:
            raise ValidationError({
                'predecessor': 'Predecessor must be in the same workflow'
            })
        
        # Validate successor is in same workflow
        if self.successor and self.successor.workflow_id != self.workflow_id:
            raise ValidationError({
                'successor': 'Successor must be in the same workflow'
            })
        
        # Validate not self-referential
        if self.predecessor and self.predecessor.id == self.id:
            raise ValidationError({
                'predecessor': 'Activity cannot be its own predecessor'
            })
        
        if self.successor and self.successor.id == self.id:
            raise ValidationError({
                'successor': 'Activity cannot be its own successor'
            })
        
        # Validate no circular dependency
        if self.predecessor and self.successor:
            if self.predecessor.id == self.successor.id:
                raise ValidationError(
                    'Circular dependency detected: predecessor and successor cannot be the same activity'
                )
    
    # Display properties for activity feed
    
    @property
    def playbook(self):
        """
        Get parent playbook for activity feed display.
        
        :returns: Parent Playbook instance
        :rtype: Playbook
        
        Example:
            >>> activity.playbook.name
            'React Development Playbook'
        """
        return self.workflow.playbook
    
    @property
    def timestamp(self):
        """
        Get most recent timestamp for activity feed display.
        
        Returns the more recent of last_accessed_at or updated_at to show
        when activity was last used (accessed) or modified.
        
        :returns: Most recent timestamp (access or update)
        :rtype: datetime
        
        Example:
            >>> activity.timestamp
            datetime.datetime(2024, 12, 4, 13, 58, 0)
        """
        if self.last_accessed_at and self.last_accessed_at > self.updated_at:
            return self.last_accessed_at
        return self.updated_at
    
    @property
    def description(self):
        """
        Get human-readable description for activity feed.
        
        :returns: Formatted description with workflow context
        :rtype: str
        
        Example:
            >>> activity.description
            'Design Component in Planning Phase workflow'
        """
        return f"{self.name} in {self.workflow.name} workflow"
    
    def get_icon_class(self):
        """
        Get Font Awesome icon class for activity feed display.
        
        :returns: Font Awesome icon class string
        :rtype: str
        
        Example:
            >>> activity.get_icon_class()
            'fas fa-tasks'
        """
        return 'fas fa-tasks'
