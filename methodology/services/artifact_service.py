"""
Service layer for Artifact operations.

Provides business logic for artifact CRUD operations, validation,
and relationship management.
"""

import logging
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from methodology.models import Artifact, ArtifactInput

logger = logging.getLogger(__name__)


class ArtifactService:
    """Service class for artifact operations."""

    @staticmethod
    def create_artifact(
        playbook,
        produced_by,
        name,
        description="",
        type="Document",
        is_required=False,
        template_file=None,
    ):
        """
        Create artifact with validation.

        :param playbook: Playbook instance
        :param produced_by: Activity instance that produces this artifact
        :param name: Artifact name as str (max 200 chars, unique per playbook). Example: "API Specification"
        :param description: Description as str. Example: "REST API contract with endpoints..."
        :param type: Type as str from ARTIFACT_TYPES. Example: "Document"
        :param is_required: Required flag as bool. Example: True
        :param template_file: File object or None
        :returns: Created Artifact instance
        :raises ValidationError: If validation fails

        Example:
            >>> artifact = ArtifactService.create_artifact(
            ...     playbook=playbook,
            ...     produced_by=activity,
            ...     name="API Specification",
            ...     type="Document",
            ...     is_required=True
            ... )
        """
        # Validate name
        if not name or not name.strip():
            logger.warning(
                f"Artifact creation failed: empty name for playbook {playbook.id}"
            )
            raise ValidationError("Artifact name cannot be empty")

        if len(name) > 200:
            logger.warning(
                f"Artifact creation failed: name too long ({len(name)} chars)"
            )
            raise ValidationError("Artifact name cannot exceed 200 characters")

        # Check for duplicate name in playbook
        if Artifact.objects.filter(playbook=playbook, name=name).exists():
            logger.warning(
                f"Artifact creation failed: duplicate name '{name}' in playbook {playbook.id}"
            )
            raise ValidationError(
                f"Artifact with name '{name}' already exists in this playbook"
            )

        # Validate type
        valid_types = [choice[0] for choice in Artifact.ARTIFACT_TYPES]
        if type not in valid_types:
            logger.warning(f"Artifact creation failed: invalid type '{type}'")
            raise ValidationError(
                f"Invalid artifact type. Must be one of: {', '.join(valid_types)}"
            )

        # Validate producer is in the playbook
        if produced_by.workflow.playbook_id != playbook.id:
            logger.warning(
                f"Producer activity {produced_by.id} not in playbook {playbook.id}"
            )
            raise ValidationError("Producer activity must be in the same playbook")

        # Create artifact
        try:
            artifact = Artifact.objects.create(
                playbook=playbook,
                produced_by=produced_by,
                name=name.strip(),
                description=description.strip() if description else "",
                type=type,
                is_required=is_required,
                template_file=template_file,
            )

            logger.info(
                f"Created artifact '{name}' (type={type}, required={is_required}) "
                f"produced by activity {produced_by.id} in playbook {playbook.id}"
            )
            return artifact

        except IntegrityError as e:
            logger.error(f"Artifact creation failed: {str(e)}")
            raise ValidationError(f"Failed to create artifact: {str(e)}")

    @staticmethod
    def get_artifact(artifact_id):
        """
        Get artifact by ID.

        :param artifact_id: Artifact primary key
        :returns: Artifact instance
        :raises Artifact.DoesNotExist: If artifact not found

        Example:
            >>> artifact = ArtifactService.get_artifact(123)
        """
        return Artifact.objects.select_related(
            "produced_by", "produced_by__workflow", "playbook"
        ).get(pk=artifact_id)

    @staticmethod
    def get_artifacts_for_playbook(playbook, type_filter=None, required_filter=None):
        """
        Get artifacts for playbook with optional filters.

        :param playbook: Playbook instance
        :param type_filter: Type filter as str or None. Example: "Document"
        :param required_filter: Required filter as bool or None. Example: True
        :returns: QuerySet of Artifact instances

        Example:
            >>> artifacts = ArtifactService.get_artifacts_for_playbook(
            ...     playbook,
            ...     type_filter="Document",
            ...     required_filter=True
            ... )
        """
        qs = (
            Artifact.objects.filter(playbook=playbook)
            .select_related("produced_by", "produced_by__workflow")
            .prefetch_related("inputs")
        )

        if type_filter:
            qs = qs.filter(type=type_filter)

        if required_filter is not None:
            qs = qs.filter(is_required=required_filter)

        return qs.order_by("produced_by__order", "name")

    @staticmethod
    def get_artifacts_for_activity(activity):
        """
        Get all artifacts produced by an activity.

        :param activity: Activity instance
        :returns: QuerySet of Artifact instances

        Example:
            >>> artifacts = ArtifactService.get_artifacts_for_activity(activity)
        """
        return Artifact.objects.filter(produced_by=activity).order_by("name")

    @staticmethod
    def search_artifacts(
        playbook, search_query=None, type_filter=None, required_filter=None, activity_filter=None
    ):
        """
        Search and filter artifacts in a playbook.

        :param playbook: Playbook instance
        :param search_query: Search term as str or None. Example: "API"
        :param type_filter: Type as str or None. Example: "Document"
        :param required_filter: Required flag as bool or None
        :param activity_filter: Activity ID as int or None
        :returns: QuerySet of Artifact instances

        Example:
            >>> ArtifactService.search_artifacts(playbook, search_query="API", type_filter="Document")
            <QuerySet [<Artifact: API Specification>]>
        """
        from django.db.models import Q

        logger.info(
            f"Searching artifacts in playbook {playbook.id}: "
            f"query='{search_query}', type='{type_filter}', "
            f"required={required_filter}, activity={activity_filter}"
        )

        # Start with all artifacts in playbook
        qs = (
            Artifact.objects.filter(playbook=playbook)
            .select_related("produced_by", "produced_by__workflow")
            .prefetch_related("inputs")
        )

        # Apply search query (search in name and description)
        if search_query:
            search_query = search_query.strip()
            qs = qs.filter(
                Q(name__icontains=search_query) | Q(description__icontains=search_query)
            )
            logger.info(f"Applied search filter: '{search_query}'")

        # Apply type filter
        if type_filter:
            qs = qs.filter(type=type_filter)
            logger.info(f"Applied type filter: '{type_filter}'")

        # Apply required filter
        if required_filter is not None:
            qs = qs.filter(is_required=required_filter)
            logger.info(f"Applied required filter: {required_filter}")

        # Apply activity filter
        if activity_filter:
            qs = qs.filter(produced_by_id=activity_filter)
            logger.info(f"Applied activity filter: {activity_filter}")

        result_count = qs.count()
        logger.info(f"Search returned {result_count} artifacts")

        return qs.order_by("produced_by__order", "name")

    @staticmethod
    def update_artifact(artifact_id, **kwargs):
        """
        Update artifact fields.

        :param artifact_id: Artifact primary key
        :param kwargs: Fields to update (name, description, type, is_required, template_file)
        :returns: Updated Artifact instance
        :raises Artifact.DoesNotExist: If artifact not found
        :raises ValidationError: If validation fails

        Example:
            >>> artifact = ArtifactService.update_artifact(
            ...     123,
            ...     name="Updated API Spec",
            ...     type="Document",
            ...     is_required=True
            ... )
        """
        artifact = Artifact.objects.get(pk=artifact_id)

        # Validate name if being updated
        if "name" in kwargs:
            new_name = kwargs["name"]
            if not new_name or not new_name.strip():
                raise ValidationError("Artifact name cannot be empty")

            if len(new_name) > 200:
                raise ValidationError("Artifact name cannot exceed 200 characters")

            # Check for duplicate name (excluding current artifact)
            if (
                Artifact.objects.filter(playbook=artifact.playbook, name=new_name)
                .exclude(pk=artifact_id)
                .exists()
            ):
                raise ValidationError(
                    f"Artifact with name '{new_name}' already exists in this playbook"
                )

            kwargs["name"] = new_name.strip()

        # Validate type if being updated
        if "type" in kwargs:
            valid_types = [choice[0] for choice in Artifact.ARTIFACT_TYPES]
            if kwargs["type"] not in valid_types:
                raise ValidationError(
                    f"Invalid artifact type. Must be one of: {', '.join(valid_types)}"
                )

        # Validate producer if being updated
        if "produced_by" in kwargs:
            new_producer = kwargs["produced_by"]
            if new_producer.workflow.playbook_id != artifact.playbook_id:
                raise ValidationError("Producer activity must be in the same playbook")

        # Strip string fields
        if "description" in kwargs and kwargs["description"]:
            kwargs["description"] = kwargs["description"].strip()

        # Update fields
        for field, value in kwargs.items():
            setattr(artifact, field, value)

        # Validate using model's clean() method
        artifact.clean()

        artifact.save()
        logger.info(f"Updated artifact {artifact_id}: {', '.join(kwargs.keys())}")

        return artifact

    @staticmethod
    def delete_artifact(artifact_id):
        """
        Delete artifact and its template file.

        :param artifact_id: Artifact primary key or Artifact instance
        :returns: Dict with deletion info
        :raises Artifact.DoesNotExist: If artifact not found

        Example:
            >>> result = ArtifactService.delete_artifact(123)
            >>> result
            {'deleted': True, 'template_deleted': True, 'consumers_cleared': 3}
        """
        # Accept either an ID or an Artifact instance
        if isinstance(artifact_id, Artifact):
            artifact = artifact_id
        else:
            artifact = Artifact.objects.get(pk=artifact_id)

        playbook_id = artifact.playbook.id
        name = artifact.name
        
        # Count consumers before deletion
        consumer_count = ArtifactInput.objects.filter(artifact=artifact).count()
        
        # Check if has template file
        has_template = bool(artifact.template_file)
        template_deleted = False
        
        # Delete template file if exists
        if has_template:
            try:
                if artifact.template_file:
                    # Delete the actual file from storage
                    artifact.template_file.delete(save=False)
                    template_deleted = True
                    logger.info(f"Deleted template file for artifact '{name}'")
            except Exception as e:
                logger.warning(f"Failed to delete template file: {str(e)}")

        # Delete artifact (cascades to ArtifactInput relationships)
        artifact.delete()
        
        logger.info(
            f"Deleted artifact '{name}' from playbook {playbook_id} "
            f"(consumers_cleared={consumer_count}, template_deleted={template_deleted})"
        )
        
        return {
            'deleted': True,
            'template_deleted': template_deleted,
            'consumers_cleared': consumer_count,
        }

    @staticmethod
    def add_artifact_input(artifact, activity, is_required=True):
        """
        Add artifact as input to an activity.

        :param artifact: Artifact instance
        :param activity: Activity instance that consumes this artifact
        :param is_required: Whether input is required. Example: True
        :returns: Created ArtifactInput instance
        :raises ValidationError: If validation fails (e.g., circular dependency)

        Example:
            >>> input = ArtifactService.add_artifact_input(
            ...     artifact=api_spec,
            ...     activity=implement_component,
            ...     is_required=True
            ... )
        """
        # Prevent circular dependency: artifact cannot be input to its producer
        if artifact.produced_by_id == activity.id:
            logger.warning(
                f"Cannot add artifact {artifact.id} as input to its producer activity {activity.id}"
            )
            raise ValidationError(
                f"Circular dependency: '{artifact.name}' is produced by '{activity.name}' "
                f"and cannot be its input"
            )

        # Check for duplicate
        if ArtifactInput.objects.filter(artifact=artifact, activity=activity).exists():
            logger.warning(
                f"Artifact {artifact.id} is already an input to activity {activity.id}"
            )
            raise ValidationError(
                f"Artifact '{artifact.name}' is already an input to activity '{activity.name}'"
            )

        try:
            artifact_input = ArtifactInput.objects.create(
                artifact=artifact, activity=activity, is_required=is_required
            )

            logger.info(
                f"Added artifact {artifact.id} as {'required' if is_required else 'optional'} "
                f"input to activity {activity.id}"
            )
            return artifact_input

        except IntegrityError as e:
            logger.error(f"Failed to add artifact input: {str(e)}")
            raise ValidationError(f"Failed to add artifact input: {str(e)}")

    @staticmethod
    def remove_artifact_input(artifact_input_id):
        """
        Remove artifact input relationship.

        :param artifact_input_id: ArtifactInput primary key
        :raises ArtifactInput.DoesNotExist: If not found

        Example:
            >>> ArtifactService.remove_artifact_input(123)
        """
        artifact_input = ArtifactInput.objects.get(pk=artifact_input_id)
        artifact_name = artifact_input.artifact.name
        activity_name = artifact_input.activity.name

        artifact_input.delete()
        logger.info(
            f"Removed artifact '{artifact_name}' as input from activity '{activity_name}'"
        )

    @staticmethod
    def get_artifact_consumers(artifact):
        """
        Get all activities that consume an artifact.

        :param artifact: Artifact instance
        :returns: QuerySet of ArtifactInput instances with related activities

        Example:
            >>> consumers = ArtifactService.get_artifact_consumers(artifact)
            >>> for input in consumers:
            ...     print(input.activity.name, input.is_required)
        """
        return (
            ArtifactInput.objects.filter(artifact=artifact)
            .select_related("activity", "activity__workflow")
            .order_by("activity__order")
        )

    @staticmethod
    def get_activity_inputs(activity):
        """
        Get all artifacts consumed by an activity.

        :param activity: Activity instance
        :returns: QuerySet of ArtifactInput instances with related artifacts

        Example:
            >>> inputs = ArtifactService.get_activity_inputs(activity)
            >>> for input in inputs:
            ...     print(input.artifact.name, input.is_required)
        """
        return (
            ArtifactInput.objects.filter(activity=activity)
            .select_related("artifact", "artifact__produced_by")
            .order_by("artifact__name")
        )
