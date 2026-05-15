"""
Playbook model for methodology management.

Playbooks represent methodologies with workflows, activities, and artifacts.
Each playbook can be owned (created by user) or downloaded from families.
"""

from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Playbook(models.Model):
    """
    Playbook represents a methodology with workflows, activities, and artifacts.
    
    Playbooks can be owned (created by user) or downloaded from families.
    Each playbook tracks versions as integer increments (v1, v2, v3).
    """
    
    # Choices
    CATEGORY_CHOICES = [
        ('product', 'Product'),
        ('development', 'Development'),
        ('research', 'Research'),
        ('design', 'Design'),
        ('other', 'Other'),
    ]
    
    VISIBILITY_CHOICES = [
        ('private', 'Private (only me)'),
        ('family', 'Family'),  # TODO: Implement family sharing
        ('local', 'Local only (not uploaded to Homebase)'),  # TODO: Implement Homebase
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('draft', 'Draft'),
        ('released', 'Released'),
        ('disabled', 'Disabled'),
    ]
    
    SOURCE_CHOICES = [
        ('owned', 'Owned'),
        ('downloaded', 'Downloaded'),
    ]
    
    # Fields
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=500)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    tags = models.JSONField(default=list, blank=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='private')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    version = models.DecimalField(max_digits=5, decimal_places=1, default=0.1, help_text="Draft: 0.1, 0.2, etc. Released: 1.0, 2.0, etc.")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='owned')
    
    # Relationships
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playbooks')
    shared_with_groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='shared_playbooks',
        help_text='Groups that have access to this playbook'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(fields=['author', 'name'], name='unique_playbook_per_author')
        ]
    
    def __str__(self):
        return f"{self.name} (v{self.version})"
    
    def is_owned_by(self, user):
        return self.author == user
    
    def can_edit(self, user):
        """
        Check if user can directly edit this playbook.
        
        Released playbooks can only be changed via PIP (Process Improvement Proposal).
        Draft playbooks can be edited directly by owner.
        
        :param user: User attempting to edit
        :returns: True if user can edit directly (not via PIP)
        """
        if not (self.source == 'owned' and self.is_owned_by(user)):
            return False
        
        # Released playbooks require PIP workflow
        if self.status == 'released':
            return False
        
        return True
    
    @property
    def is_draft(self):
        """Check if playbook is in draft status."""
        return self.status == 'draft'
    
    @property
    def is_released(self):
        """Check if playbook is released (requires PIP for changes)."""
        return self.status == 'released'
    
    def increment_version(self):
        """
        Increment playbook version based on status.
        
        Draft: 0.1 → 0.2 → 0.3, etc.
        Released: 1.0 → 2.0 → 3.0, etc. (via PIP only)
        
        :returns: New version number
        """
        # Ensure version is Decimal for arithmetic
        current_version = Decimal(str(self.version))
        
        if self.is_draft:
            # Increment by 0.1 for draft changes
            self.version = current_version + Decimal('0.1')
        else:
            # For released, increment by 1.0 (should only happen via PIP)
            self.version = current_version + Decimal('1.0')
        
        return self.version
    
    def compute_next_major_line_version(self) -> Decimal:
        """
        Next major line from the current playbook version (X.Y → next integer major).

        Examples: 0.9 → 1.0, 1.0 → 2.0, 1.3 → 2.0.

        :returns: Decimal major version with one decimal place
        """
        current = Decimal(str(self.version))
        whole = int(current)
        return Decimal(whole + 1).quantize(Decimal("0.1"))
    
    def get_quick_stats(self):
        """
        Get quick statistics for the playbook dashboard.
        
        Returns dictionary with counts of related objects.
        
        :returns: Dictionary with stat counts
        :rtype: dict
        """
        from methodology.models.activity import Activity
        from methodology.models.artifact import Artifact

        activity_qs = Activity.objects.filter(workflow__playbook=self)
        return {
            'workflows': self.workflows.count(),
            'phases': self.phases.count(),  # Count Phase objects in playbook
            'activities': activity_qs.count(),
            'artifacts': Artifact.objects.filter(playbook=self).count(),
            'agents': self.agents.count(),
            'skills': self.skills.count(),
            'rules': self.rules.count(),
        }
    
    def get_status_badge_color(self):
        """
        Get Bootstrap color class for status badge.
        
        Maps playbook status to Bootstrap badge color.
        
        :returns: Bootstrap color class name
        :rtype: str
        """
        status_colors = {
            'active': 'success',
            'draft': 'warning',
            'released': 'primary',
            'disabled': 'secondary'
        }
        return status_colors.get(self.status, 'secondary')
