"""
Artifact model for methodology deliverables.

Artifacts are outputs produced by activities that can be consumed as inputs
by downstream activities in the workflow.
"""

from django.db import models
from django.core.exceptions import ValidationError


class Artifact(models.Model):
    """
    Artifact represents a deliverable produced by an activity.

    Each artifact has exactly one producer (the activity that creates it)
    and can have multiple consumers (activities that use it as input).
    """

    # Type choices
    ARTIFACT_TYPES = [
        ("Document", "Document"),
        ("Template", "Template"),
        ("Code", "Code"),
        ("Diagram", "Diagram"),
        ("Data", "Data"),
        ("Reference Architecture", "Reference Architecture"),
        ("Other", "Other"),
    ]

    # Core fields
    name = models.CharField(
        max_length=200, help_text="Artifact name. Example: 'API Specification'"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description. Example: 'REST API contract with endpoints...'",
    )
    type = models.CharField(
        max_length=50,
        choices=ARTIFACT_TYPES,
        default="Document",
        help_text="Artifact type. Example: 'Document'",
    )
    is_required = models.BooleanField(
        default=False, help_text="Whether this artifact is required. Example: True"
    )

    # Producer relationship (1:1 - every artifact has exactly one producer)
    produced_by = models.ForeignKey(
        "Activity",
        on_delete=models.CASCADE,
        related_name="output_artifacts",
        help_text="Activity that produces this artifact as output",
    )

    # For breadcrumbs and context (denormalized for performance)
    playbook = models.ForeignKey(
        "Playbook",
        on_delete=models.CASCADE,
        related_name="artifacts",
        help_text="Playbook containing this artifact (via activity->workflow->playbook)",
    )

    # Template file (optional)
    template_file = models.FileField(
        upload_to="artifacts/templates/",
        blank=True,
        null=True,
        help_text="Optional template file. Example: 'component_template.tsx'",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["playbook", "produced_by", "name"]
        verbose_name = "Artifact"
        verbose_name_plural = "Artifacts"
        constraints = [
            models.UniqueConstraint(
                fields=["playbook", "name"],
                name="unique_artifact_per_playbook",
                violation_error_message="An artifact with this name already exists in this playbook",
            )
        ]
        indexes = [
            models.Index(fields=["playbook", "type"]),
            models.Index(fields=["produced_by"]),
            models.Index(fields=["is_required"]),
        ]

    def __str__(self):
        """
        String representation.

        :returns: Artifact name as str. Example: "API Specification"
        """
        return self.name

    def clean(self):
        """
        Model-level validation.

        :raises ValidationError: If validation fails
        """
        # Validate name
        if not self.name or not self.name.strip():
            raise ValidationError({"name": "Artifact name cannot be empty"})

        # Validate type
        valid_types = [choice[0] for choice in self.ARTIFACT_TYPES]
        if self.type not in valid_types:
            raise ValidationError(
                {
                    "type": f"Invalid artifact type. Must be one of: {', '.join(valid_types)}"
                }
            )

        # Auto-set playbook from producer activity if not set
        # Use _id to avoid database query, then load the full object if needed
        if self.produced_by_id and not self.playbook_id:
            # Need to load produced_by to access its workflow
            if not self.produced_by:
                from methodology.models import Activity

                self.produced_by = Activity.objects.select_related(
                    "workflow__playbook"
                ).get(pk=self.produced_by_id)
            self.playbook = self.produced_by.workflow.playbook

    def save(self, *args, **kwargs):
        """
        Override save to run validation.

        :param args: Positional arguments
        :param kwargs: Keyword arguments
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Get URL for artifact detail page.

        :returns: URL path as str. Example: "/artifacts/123/"
        """
        from django.urls import reverse

        return reverse("artifact_detail", kwargs={"pk": self.pk})

    def get_producer_link(self):
        """
        Get URL for producer activity.

        :returns: URL path as str. Example: "/activities/45/"
        """
        return self.produced_by.get_absolute_url()

    def get_consumers(self):
        """
        Get all activities that consume this artifact as input.

        :returns: QuerySet of ArtifactInput instances
        """
        return self.inputs.all()

    def get_consumer_count(self):
        """
        Get count of activities consuming this artifact.

        :returns: int count. Example: 3
        """
        return self.inputs.count()

    def get_playbook_link(self):
        """
        Get URL for parent playbook.

        :returns: URL path as str. Example: "/playbooks/12/"
        """
        return self.playbook.get_absolute_url()

    def has_template(self):
        """
        Check if artifact has template file.

        :returns: bool. Example: True
        """
        return bool(self.template_file)

    def get_template_filename(self):
        """
        Get template filename if exists.

        :returns: str or None. Example: "component_template.tsx"
        """
        if self.template_file:
            return self.template_file.name.split("/")[-1]
        return None

    def to_dict(self):
        """
        Convert to dictionary for API/MCP responses.

        :returns: Dict representation. Example: {"id": 1, "name": "API Spec", "type": "Document", ...}
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "is_required": self.is_required,
            "has_template": self.has_template(),
            "template_filename": self.get_template_filename(),
            "produced_by_id": self.produced_by_id,
            "produced_by_name": self.produced_by.name,
            "consumer_count": self.get_consumer_count(),
            "playbook_id": self.playbook_id,
            "playbook_name": self.playbook.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
