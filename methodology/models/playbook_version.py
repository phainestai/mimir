"""
PlaybookVersion model for tracking version history.

Versions use semantic X.Y (Decimal): draft lines (0.x), released lines (1.x, 2.x, …).
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class VersionSource(models.TextChoices):
    AUTHOR = "author", "Author"
    RELEASE = "release", "Release"
    PIP_SOURCE = "pip", "PIP"
    ADMIN = "admin", "Admin"


class PlaybookVersion(models.Model):
    """Tracks version history for playbooks."""

    playbook = models.ForeignKey(
        "Playbook", on_delete=models.CASCADE, related_name="versions"
    )
    version_number = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[MinValueValidator(Decimal("0"))],
    )
    snapshot_data = models.JSONField()
    change_summary = models.TextField(blank=True)
    description = models.TextField(
        blank=True,
        default="",
        help_text="Release or change narrative; aligns with change_summary over time.",
    )
    is_major = models.BooleanField(
        default=False,
        help_text="True when this row records a Release major bump.",
    )
    source = models.CharField(
        max_length=20,
        choices=VersionSource.choices,
        default=VersionSource.AUTHOR,
    )
    pip = models.ForeignKey(
        "ProcessImprovementProposal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="playbook_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["playbook", "version_number"],
                name="unique_version_per_playbook",
            )
        ]

    def __str__(self):
        return f"{self.playbook.name} v{self.version_number}"
