"""
Rule model for playbook-scoped Cursor/IDE-style guidance.

Rules are attached to multiple activities via M2M. Export writes .mdc-compatible files.
"""

from django.db import models


class Rule(models.Model):
    """
    Playbook-scoped rule (IDE rule file content).

    One rule can be linked to many activities within the same playbook.
    """

    playbook = models.ForeignKey(
        'Playbook',
        on_delete=models.CASCADE,
        related_name='rules',
        help_text='Parent playbook owning this rule',
    )
    title = models.CharField(max_length=200, help_text='Short title for the rule')
    slug = models.SlugField(
        max_length=220,
        help_text='Filename-safe identifier, unique per playbook',
    )
    content = models.TextField(
        blank=True,
        default='',
        help_text='Markdown body (exported after YAML front matter)',
    )
    always_apply = models.BooleanField(
        default=True,
        help_text='When True, exported .mdc includes alwaysApply in front matter',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['playbook', 'slug']
        verbose_name = 'Rule'
        verbose_name_plural = 'Rules'
        constraints = [
            models.UniqueConstraint(fields=['playbook', 'slug'], name='unique_rule_slug_per_playbook'),
        ]

    def __str__(self):
        return f'{self.title} ({self.slug})'

    def is_owned_by(self, user):
        """True if playbook is owned by user."""
        return self.playbook.is_owned_by(user)
