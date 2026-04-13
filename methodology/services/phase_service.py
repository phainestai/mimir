"""
Service layer for Phase operations.

All business logic for Phase CRUD lives here so that both the Django views
and the MCP tools share the same code path.  Views and MCP tools never
touch the ORM directly for Phase operations.
"""

import logging

from django.core.exceptions import ValidationError

from methodology.models import Phase, Workflow

logger = logging.getLogger(__name__)


class PhaseService:
    """Business-logic service for Phase entities."""

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    @staticmethod
    def create_phase(workflow: Workflow, name: str, description: str = '', order: int = None) -> Phase:
        """
        Create a new Phase inside *workflow*.

        Auto-assigns *order* as (max_existing_order + 1) when not provided.
        Strips whitespace from *name*.

        :param workflow: Parent Workflow instance.
            Example: Workflow(id=5, name="Component Development")
        :param name: Phase name, unique within the workflow.
            Example: "Planning"
        :param description: Optional description.
            Example: "Initial planning and requirements gathering"
        :param order: Explicit sort position (1-based). Auto-assigned if None.
            Example: 2
        :returns: Newly created Phase instance.
        :raises ValidationError: If name is blank or already exists in workflow.

        Example:
            >>> phase = PhaseService.create_phase(workflow, "Planning")
            >>> phase.id
            1
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    @staticmethod
    def get_phases_for_workflow(workflow: Workflow):
        """
        Return all phases for *workflow* ordered by *order* asc.

        :param workflow: Parent Workflow instance.
        :returns: QuerySet of Phase ordered by order.

        Example:
            >>> phases = PhaseService.get_phases_for_workflow(wf)
            >>> [p.name for p in phases]
            ['Planning', 'Execution', 'Testing']
        """
        raise NotImplementedError()

    @staticmethod
    def get_phase_by_id(phase_id: int) -> Phase:
        """
        Return Phase with *phase_id* or raise ValueError.

        :param phase_id: Primary key of the Phase.
            Example: 42
        :returns: Phase instance.
        :raises ValueError: If no Phase with that id exists.

        Example:
            >>> phase = PhaseService.get_phase_by_id(42)
            >>> phase.name
            'Planning'
        """
        raise NotImplementedError()

    @staticmethod
    def get_phase_by_name(workflow: Workflow, name: str) -> Phase:
        """
        Return Phase matching *name* (case-insensitive) in *workflow*, or None.

        :param workflow: Parent Workflow instance.
        :param name: Phase name to look up.
            Example: "planning"
        :returns: Phase instance or None.

        Example:
            >>> phase = PhaseService.get_phase_by_name(wf, "planning")
            >>> phase.name
            'Planning'
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    @staticmethod
    def update_phase(phase: Phase, **kwargs) -> Phase:
        """
        Update fields on *phase*.

        Accepted keyword arguments: name, description, order.
        Strips whitespace from name if provided.

        :param phase: Phase instance to update.
        :param kwargs: Fields to update.
            Example: name="Requirements & Planning", order=2
        :returns: Updated Phase instance.
        :raises ValidationError: If updated name conflicts with existing phase.

        Example:
            >>> updated = PhaseService.update_phase(phase, name="Requirements & Planning")
            >>> updated.name
            'Requirements & Planning'
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------
    # Deletion
    # ------------------------------------------------------------------

    @staticmethod
    def delete_phase(phase: Phase) -> None:
        """
        Delete *phase* and move its activities to unassigned (phase FK = NULL).

        Also renumbers remaining phases in the parent workflow so orders
        remain contiguous starting from 1.

        :param phase: Phase instance to delete.
        :returns: None

        Example:
            >>> PhaseService.delete_phase(phase)
            # phase is deleted; its activities have phase_fk=None
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------
    # Reordering
    # ------------------------------------------------------------------

    @staticmethod
    def reorder_phases(workflow: Workflow, ordered_ids: list) -> list:
        """
        Reorder phases in *workflow* according to *ordered_ids*.

        Sets phase.order = position (1-based) for each id in *ordered_ids*.

        :param workflow: Parent Workflow instance.
        :param ordered_ids: Phase IDs in desired order.
            Example: [3, 1, 2]
        :returns: List of updated Phase instances in new order.
        :raises ValueError: If any id does not belong to *workflow*.

        Example:
            >>> phases = PhaseService.reorder_phases(wf, [3, 1, 2])
            >>> [p.order for p in phases]
            [1, 2, 3]
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------
    # Migration helper
    # ------------------------------------------------------------------

    @staticmethod
    def migrate_string_phases(workflow: Workflow) -> dict:
        """
        Convert Activity.phase string values to Phase FK relationships.

        For each unique non-blank Activity.phase string in *workflow*:
        - Create a Phase with that name (order = alphabetical index + 1).
        - Set activity.phase_fk = the newly-created Phase.

        Idempotent: skips activities that already have phase_fk set.

        :param workflow: Workflow whose activities to migrate.
        :returns: Dict mapping phase name → Phase instance.
            Example: {'Planning': Phase(id=1), 'Execution': Phase(id=2)}

        Example:
            >>> result = PhaseService.migrate_string_phases(wf)
            >>> result.keys()
            dict_keys(['Planning', 'Execution'])
        """
        raise NotImplementedError()
