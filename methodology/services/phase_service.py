"""
PhaseService for managing Phase CRUD operations.

Handles creation, updating, deletion, and retrieval of phases within playbooks.
"""

import logging
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.db import models

from methodology.models import Phase, Playbook

logger = logging.getLogger(__name__)


class PhaseService:
    """Service for managing Phase entities."""
    
    @staticmethod
    def create_phase(playbook_id, name, description, order, user):
        """
        Create a new phase in a playbook.
        
        :param playbook_id: ID of parent playbook. Example: 1
        :param name: Phase name. Example: "Inception"
        :param description: Phase description. Example: "ESM & DTA & DSP focused"
        :param order: Display order. Example: 1
        :param user: User creating the phase
        :returns: Created Phase instance
        :rtype: Phase
        :raises PermissionDenied: If user doesn't own playbook or playbook is released
        :raises ValidationError: If validation fails
        
        Example:
            >>> phase = PhaseService.create_phase(
            ...     playbook_id=1,
            ...     name="Inception",
            ...     description="ESM & DTA & DSP focused",
            ...     order=1,
            ...     user=maria
            ... )
            >>> phase.name
            'Inception'
        """
        logger.info(f"Creating phase '{name}' in playbook {playbook_id} for user {user.email}")
        
        try:
            playbook = Playbook.objects.get(id=playbook_id)
        except Playbook.DoesNotExist:
            logger.error(f"Playbook {playbook_id} not found")
            raise ValidationError(f"Playbook with id {playbook_id} not found")
        
        # Check permissions
        if not playbook.is_owned_by(user):
            logger.warning(f"User {user.email} attempted to create phase in playbook {playbook_id} they don't own")
            raise PermissionDenied("You don't have permission to modify this playbook")
        
        if not playbook.can_edit(user):
            logger.warning(f"User {user.email} attempted to create phase in released playbook {playbook_id}")
            raise PermissionDenied("Cannot modify released playbook. Submit a PIP instead.")
        
        # Check for duplicate name
        if Phase.objects.filter(playbook=playbook, name=name).exists():
            logger.warning(f"Phase with name '{name}' already exists in playbook {playbook_id}")
            raise ValidationError(f"Phase with name '{name}' already exists in this playbook")
        
        # Create phase
        with transaction.atomic():
            # Auto-assign order if not provided
            if order is None:
                max_order = Phase.objects.filter(playbook=playbook).aggregate(
                    models.Max('order')
                )['order__max']
                order = (max_order or 0) + 1
            
            phase = Phase.objects.create(
                playbook=playbook,
                name=name,
                description=description or "",
                order=order
            )
            
            # Increment playbook version
            playbook.increment_version()
            
            logger.info(f"Created phase {phase.id} '{phase.name}' in playbook {playbook_id}")
            return phase
    
    @staticmethod
    def update_phase(phase_id, name=None, description=None, order=None, user=None):
        """
        Update an existing phase.
        
        :param phase_id: Phase ID. Example: 1
        :param name: New name (optional). Example: "Elaboration"
        :param description: New description (optional)
        :param order: New order (optional). Example: 2
        :param user: User updating the phase
        :returns: Updated Phase instance
        :rtype: Phase
        :raises PermissionDenied: If user doesn't own playbook or playbook is released
        :raises ValidationError: If phase not found
        
        Example:
            >>> phase = PhaseService.update_phase(
            ...     phase_id=1,
            ...     name="Elaboration Updated",
            ...     order=2,
            ...     user=maria
            ... )
        """
        logger.info(f"Updating phase {phase_id} for user {user.email}")
        
        try:
            phase = Phase.objects.select_related('playbook').get(id=phase_id)
        except Phase.DoesNotExist:
            logger.error(f"Phase {phase_id} not found")
            raise ValidationError(f"Phase with id {phase_id} not found")
        
        # Check permissions
        if not phase.is_owned_by(user):
            logger.warning(f"User {user.email} attempted to update phase {phase_id} they don't own")
            raise PermissionDenied("You don't have permission to modify this phase")
        
        if not phase.can_edit(user):
            logger.warning(f"User {user.email} attempted to update phase in released playbook")
            raise PermissionDenied("Cannot modify released playbook. Submit a PIP instead.")
        
        # Update fields
        with transaction.atomic():
            if name is not None:
                phase.name = name
            if description is not None:
                phase.description = description
            if order is not None:
                phase.order = order
            
            phase.save()
            
            # Increment playbook version
            phase.playbook.increment_version()
            
            logger.info(f"Updated phase {phase_id}")
            return phase
    
    @staticmethod
    def delete_phase(phase_id, user):
        """
        Delete a phase.
        
        :param phase_id: Phase ID. Example: 1
        :param user: User deleting the phase
        :returns: Dict with deleted=True
        :rtype: dict
        :raises PermissionDenied: If user doesn't own playbook or playbook is released
        :raises ValidationError: If phase has activities assigned
        
        Example:
            >>> result = PhaseService.delete_phase(phase_id=1, user=maria)
            >>> result['deleted']
            True
        """
        logger.info(f"Deleting phase {phase_id} for user {user.email}")
        
        try:
            phase = Phase.objects.select_related('playbook').get(id=phase_id)
        except Phase.DoesNotExist:
            logger.error(f"Phase {phase_id} not found")
            raise ValidationError(f"Phase with id {phase_id} not found")
        
        # Check permissions
        if not phase.is_owned_by(user):
            logger.warning(f"User {user.email} attempted to delete phase {phase_id} they don't own")
            raise PermissionDenied("You don't have permission to modify this phase")
        
        if not phase.can_edit(user):
            logger.warning(f"User {user.email} attempted to delete phase in released playbook")
            raise PermissionDenied("Cannot modify released playbook. Submit a PIP instead.")
        
        # Check if phase has activities
        activity_count = phase.get_activity_count()
        if activity_count > 0:
            logger.warning(f"Cannot delete phase {phase_id} - has {activity_count} activities assigned")
            raise ValidationError(f"Cannot delete phase with {activity_count} activities assigned. Reassign activities first.")
        
        # Delete phase
        with transaction.atomic():
            playbook = phase.playbook
            phase.delete()
            
            # Increment playbook version
            playbook.increment_version()
            
            logger.info(f"Deleted phase {phase_id}")
            return {'deleted': True}
    
    @staticmethod
    def list_phases(playbook_id, user):
        """
        List all phases in a playbook.
        
        :param playbook_id: Playbook ID. Example: 1
        :param user: User requesting the list
        :returns: QuerySet of Phase objects
        :rtype: QuerySet
        :raises ValidationError: If playbook not found
        :raises PermissionDenied: If user doesn't have permission to view playbook
        
        Example:
            >>> phases = PhaseService.list_phases(playbook_id=1, user=maria)
            >>> len(phases)
            5
        """
        logger.info(f"Listing phases for playbook {playbook_id} for user {user.email}")
        
        try:
            playbook = Playbook.objects.get(id=playbook_id)
        except Playbook.DoesNotExist:
            logger.error(f"Playbook {playbook_id} not found")
            raise ValidationError(f"Playbook with id {playbook_id} not found")
        
        # Check permissions: owned playbooks require ownership, downloaded playbooks are viewable by all
        if playbook.source == 'owned' and not playbook.is_owned_by(user):
            logger.warning(f"User {user.email} attempted to list phases in owned playbook {playbook_id} they don't own")
            raise PermissionDenied("You don't have permission to view this playbook")
        
        # Downloaded playbooks are viewable by everyone (no permission check needed)
        
        phases = Phase.objects.filter(playbook=playbook).order_by('order', 'name')
        logger.info(f"Found {phases.count()} phases in playbook {playbook_id} (source={playbook.source})")
        
        return phases
    
    @staticmethod
    def get_phase_with_activities(phase_id, user):
        """
        Get phase details with activities grouped by workflow.
        
        :param phase_id: Phase ID. Example: 1
        :param user: User requesting the phase
        :returns: Dict with phase and workflow_activities
        :rtype: dict
        :raises ValidationError: If phase not found
        :raises PermissionDenied: If user doesn't own playbook
        
        Example:
            >>> result = PhaseService.get_phase_with_activities(phase_id=1, user=maria)
            >>> result['phase'].name
            'Inception'
            >>> len(result['workflow_activities'])
            3  # 3 workflows have activities in this phase
        """
        logger.info(f"Getting phase {phase_id} with activities for user {user.email}")
        
        try:
            phase = Phase.objects.select_related('playbook').get(id=phase_id)
        except Phase.DoesNotExist:
            logger.error(f"Phase {phase_id} not found")
            raise ValidationError(f"Phase with id {phase_id} not found")
        
        # Check permissions
        if not phase.is_owned_by(user):
            logger.warning(f"User {user.email} attempted to view phase {phase_id} they don't own")
            raise PermissionDenied("You don't have permission to view this phase")
        
        # Get activities grouped by workflow
        workflow_activities = phase.get_workflows_with_activities()
        
        logger.info(f"Retrieved phase {phase_id} with {len(workflow_activities)} workflows")
        
        return {
            'phase': phase,
            'workflow_activities': workflow_activities,
            'artifacts': phase.get_artifacts()
        }
    
    @staticmethod
    def reorder_phases(playbook_id, phase_order_list, user):
        """
        Reorder phases in a playbook.
        
        :param playbook_id: Playbook ID. Example: 1
        :param phase_order_list: List of (phase_id, new_order) tuples. Example: [(1, 1), (2, 2), (3, 3)]
        :param user: User reordering phases
        :returns: List of updated Phase instances
        :rtype: list
        :raises ValidationError: If playbook or phases not found
        :raises PermissionDenied: If user doesn't own playbook or playbook is released
        
        Example:
            >>> phases = PhaseService.reorder_phases(
            ...     playbook_id=1,
            ...     phase_order_list=[(3, 1), (1, 2), (2, 3)],
            ...     user=maria
            ... )
        """
        logger.info(f"Reordering phases in playbook {playbook_id} for user {user.email}")
        
        try:
            playbook = Playbook.objects.get(id=playbook_id)
        except Playbook.DoesNotExist:
            logger.error(f"Playbook {playbook_id} not found")
            raise ValidationError(f"Playbook with id {playbook_id} not found")
        
        # Check permissions
        if not playbook.is_owned_by(user):
            logger.warning(f"User {user.email} attempted to reorder phases in playbook {playbook_id} they don't own")
            raise PermissionDenied("You don't have permission to modify this playbook")
        
        if not playbook.can_edit(user):
            logger.warning(f"User {user.email} attempted to reorder phases in released playbook")
            raise PermissionDenied("Cannot modify released playbook. Submit a PIP instead.")
        
        # Update phase orders
        with transaction.atomic():
            # First pass: set all to temporary negative orders to avoid unique constraint violations
            phases_to_update = []
            for idx, (phase_id, new_order) in enumerate(phase_order_list):
                try:
                    phase = Phase.objects.get(id=phase_id, playbook=playbook)
                    phase.order = -(idx + 1)  # Temporary negative order
                    phase.save()
                    phases_to_update.append((phase, new_order))
                except Phase.DoesNotExist:
                    logger.error(f"Phase {phase_id} not found in playbook {playbook_id}")
                    raise ValidationError(f"Phase {phase_id} not found in playbook")
            
            # Second pass: set final orders
            updated_phases = []
            for phase, new_order in phases_to_update:
                phase.order = new_order
                phase.save()
                updated_phases.append(phase)
            
            # Increment playbook version
            playbook.increment_version()
            
            logger.info(f"Reordered {len(updated_phases)} phases in playbook {playbook_id}")
            return updated_phases
