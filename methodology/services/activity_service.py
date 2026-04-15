"""
Service layer for Activity operations.

Provides business logic for activity CRUD operations, validation,
grouping functionality, and skill/agent link management.
"""

import logging
from django.db import IntegrityError
from django.db import models
from django.core.exceptions import ValidationError
from methodology.models import Activity, Skill, Agent

logger = logging.getLogger(__name__)


class ActivityService:
    """Service class for activity operations."""
    
    @staticmethod
    def create_activity(workflow, name, guidance='', phase=None, order=None, 
                       predecessor=None, successor=None):
        """
        Create activity with validation and auto-order.
        
        :param workflow: Parent workflow instance
        :param name: Activity name (max 200 chars, unique within workflow)
        :param guidance: Rich Markdown guidance with instructions, examples, diagrams (optional)
        :param phase: Phase grouping (optional)
        :param order: Execution order (auto-assigned if None)
        :param predecessor: Previous activity (must be in same workflow)
        :param successor: Next activity (must be in same workflow)
        :returns: Created Activity instance
        :raises ValidationError: If validation fails
        
        Example:
            >>> activity = ActivityService.create_activity(
            ...     workflow=wf,
            ...     name="Design Component",
            ...     guidance="## Steps\n1. Review requirements\n2. Create mockup",
            ...     phase="Planning",
            ...     predecessor=previous_activity
            ... )
        """
        # Validate name
        if not name or not name.strip():
            logger.warning(f"Activity creation failed: empty name for workflow {workflow.id}")
            raise ValidationError("Activity name cannot be empty")
        
        if len(name) > 200:
            logger.warning(f"Activity creation failed: name too long ({len(name)} chars)")
            raise ValidationError("Activity name cannot exceed 200 characters")
        
        # Check for duplicate name in workflow
        if Activity.objects.filter(workflow=workflow, name=name).exists():
            logger.warning(f"Activity creation failed: duplicate name '{name}' in workflow {workflow.id}")
            raise ValidationError(f"Activity with name '{name}' already exists in this workflow")
        
        # Auto-assign order if not provided
        if order is None:
            max_order = Activity.objects.filter(workflow=workflow).aggregate(
                models.Max('order')
            )['order__max']
            order = (max_order or 0) + 1
        
        # Validate dependencies are in same workflow
        if predecessor and predecessor.workflow_id != workflow.id:
            logger.warning(f"Predecessor {predecessor.id} not in workflow {workflow.id}")
            raise ValidationError("Predecessor must be in the same workflow")
        
        if successor and successor.workflow_id != workflow.id:
            logger.warning(f"Successor {successor.id} not in workflow {workflow.id}")
            raise ValidationError("Successor must be in the same workflow")
        
        # Create activity
        try:
            activity = Activity.objects.create(
                workflow=workflow,
                name=name.strip(),
                guidance=guidance.strip() if guidance else '',
                phase=phase.strip() if phase else None,
                order=order,
                predecessor=predecessor,
                successor=successor
            )
            
            dep_info = []
            if predecessor:
                dep_info.append(f"predecessor={predecessor.reference_name}")
            if successor:
                dep_info.append(f"successor={successor.reference_name}")
            dep_str = f" with {', '.join(dep_info)}" if dep_info else ""
            
            logger.info(f"Created activity '{name}' (#{order}) in workflow {workflow.id}{dep_str}")
            return activity
            
        except IntegrityError as e:
            logger.error(f"Activity creation failed: {str(e)}")
            raise ValidationError(f"Failed to create activity: {str(e)}")
    
    @staticmethod
    def get_activity(activity_id):
        """
        Get activity by ID.
        
        :param activity_id: Activity primary key
        :returns: Activity instance
        :raises Activity.DoesNotExist: If activity not found
        
        Example:
            >>> activity = ActivityService.get_activity(123)
        """
        return Activity.objects.select_related('workflow', 'workflow__playbook').get(pk=activity_id)
    
    @staticmethod
    def get_activities_for_workflow(workflow):
        """
        Get all activities in a workflow, ordered.
        
        :param workflow: Workflow instance
        :returns: QuerySet of Activity instances ordered by order, name
        
        Example:
            >>> activities = ActivityService.get_activities_for_workflow(wf)
            >>> for act in activities:
            ...     print(act.name, act.order)
        """
        return Activity.objects.filter(workflow=workflow).select_related(
            'predecessor', 'successor'
        ).order_by('order', 'name')
    
    @staticmethod
    def get_activities_grouped_by_phase(workflow):
        """
        Get activities grouped by phase.
        
        :param workflow: Workflow instance
        :returns: Dict mapping phase names to lists of activities
        
        Example:
            >>> grouped = ActivityService.get_activities_grouped_by_phase(wf)
            >>> grouped
            {
                'Planning': [<Activity: Design (#1)>, <Activity: Spec (#2)>],
                'Execution': [<Activity: Code (#3)>],
                'Unassigned': [<Activity: Review (#4)>]
            }
        """
        activities = ActivityService.get_activities_for_workflow(workflow)
        grouped = {}
        
        for activity in activities:
            phase_name = activity.get_phase_display_name()
            if phase_name not in grouped:
                grouped[phase_name] = []
            grouped[phase_name].append(activity)
        
        return grouped
    
    @staticmethod
    def update_activity(activity_id, **kwargs):
        """
        Update activity fields.
        
        :param activity_id: Activity primary key
        :param kwargs: Fields to update (name, guidance, order, phase, predecessor, successor)
        :returns: Updated Activity instance
        :raises Activity.DoesNotExist: If activity not found
        :raises ValidationError: If validation fails
        
        Example:
            >>> activity = ActivityService.update_activity(
            ...     123,
            ...     name="New Name",
            ...     phase="Execution",
            ...     predecessor=prev_activity
            ... )
        """
        activity = Activity.objects.get(pk=activity_id)
        
        # Validate name if being updated
        if 'name' in kwargs:
            new_name = kwargs['name']
            if not new_name or not new_name.strip():
                raise ValidationError("Activity name cannot be empty")
            
            if len(new_name) > 200:
                raise ValidationError("Activity name cannot exceed 200 characters")
            
            # Check for duplicate name (excluding current activity)
            if Activity.objects.filter(
                workflow=activity.workflow,
                name=new_name
            ).exclude(pk=activity_id).exists():
                raise ValidationError(f"Activity with name '{new_name}' already exists in this workflow")
            
            kwargs['name'] = new_name.strip()
        
        # Validate dependencies if being updated
        if 'predecessor' in kwargs and kwargs['predecessor']:
            if kwargs['predecessor'].workflow_id != activity.workflow_id:
                raise ValidationError("Predecessor must be in the same workflow")
        
        if 'successor' in kwargs and kwargs['successor']:
            if kwargs['successor'].workflow_id != activity.workflow_id:
                raise ValidationError("Successor must be in the same workflow")
        
        # Strip string fields
        if 'guidance' in kwargs and kwargs['guidance']:
            kwargs['guidance'] = kwargs['guidance'].strip()
        
        if 'phase' in kwargs and kwargs['phase']:
            kwargs['phase'] = kwargs['phase'].strip()
        
        # Update fields
        for field, value in kwargs.items():
            setattr(activity, field, value)
        
        # Validate using model's clean() method
        activity.clean()
        
        activity.save()
        logger.info(f"Updated activity {activity_id}: {', '.join(kwargs.keys())}")
        
        return activity
    
    @staticmethod
    def delete_activity(activity_id):
        """
        Delete activity.
        
        :param activity_id: Activity primary key
        :raises Activity.DoesNotExist: If activity not found
        
        Example:
            >>> ActivityService.delete_activity(123)
        """
        activity = Activity.objects.get(pk=activity_id)
        workflow_id = activity.workflow.id
        name = activity.name
        
        activity.delete()
        logger.info(f"Deleted activity '{name}' from workflow {workflow_id}")
    
    @staticmethod
    def duplicate_activity(activity_id, new_name=None):
        """
        Create a copy of an activity.
        
        :param activity_id: Activity primary key to duplicate
        :param new_name: Name for duplicate (default: "Copy of [original name]")
        :returns: New Activity instance
        :raises Activity.DoesNotExist: If activity not found
        :raises ValidationError: If validation fails
        
        Example:
            >>> dup = ActivityService.duplicate_activity(123, "Component Design v2")
        """
        original = Activity.objects.get(pk=activity_id)
        
        # Generate name for duplicate
        if new_name is None:
            new_name = f"Copy of {original.name}"
        
        # Get next order
        max_order = Activity.objects.filter(workflow=original.workflow).aggregate(
            models.Max('order')
        )['order__max']
        next_order = (max_order or 0) + 1
        
        # Create duplicate (without dependencies to avoid conflicts)
        return ActivityService.create_activity(
            workflow=original.workflow,
            name=new_name,
            guidance=original.guidance,
            phase=original.phase,
            order=next_order
        )
    
    @staticmethod
    def get_available_predecessors(workflow, exclude_activity_id=None):
        """
        Get activities that can be predecessors.
        
        :param workflow: Workflow instance
        :param exclude_activity_id: Activity ID to exclude (usually current activity)
        :returns: QuerySet of available activities
        
        Example:
            >>> predecessors = ActivityService.get_available_predecessors(wf, exclude_activity_id=123)
        """
        qs = Activity.objects.filter(workflow=workflow).order_by('order')
        if exclude_activity_id:
            qs = qs.exclude(pk=exclude_activity_id)
        return qs
    
    @staticmethod
    def get_available_successors(workflow, exclude_activity_id=None):
        """
        Get activities that can be successors.
        
        :param workflow: Workflow instance
        :param exclude_activity_id: Activity ID to exclude (usually current activity)
        :returns: QuerySet of available activities
        
        Example:
            >>> successors = ActivityService.get_available_successors(wf, exclude_activity_id=123)
        """
        qs = Activity.objects.filter(workflow=workflow).order_by('order')
        if exclude_activity_id:
            qs = qs.exclude(pk=exclude_activity_id)
        return qs
    
    @staticmethod
    def touch_activity_access(activity_id):
        """
        Update last_accessed_at timestamp when activity is viewed.
        
        :param activity_id: Activity primary key
        :return: None
        :raises Activity.DoesNotExist: If activity not found
        
        Example:
            >>> ActivityService.touch_activity_access(123)
        """
        from django.utils import timezone
        
        try:
            activity = Activity.objects.get(pk=activity_id)
            activity.last_accessed_at = timezone.now()
            activity.save(update_fields=['last_accessed_at'])
            logger.info(f"Activity {activity_id} accessed at {activity.last_accessed_at}")
        except Activity.DoesNotExist:
            logger.error(f"Activity {activity_id} not found for access tracking")
            raise  # Propagate to caller
    
    @staticmethod
    def get_recent_activities(user, limit=10):
        """
        Get recently used/modified activities sorted by most recent access or update.
        
        Sorts by MAX(last_accessed_at, updated_at) to show activities that were
        either recently accessed via MCP or modified via GUI/MCP.
        
        :param user: User instance
        :param limit: Maximum number of activities to return (default: 10)
        :return: QuerySet of Activity instances ordered by recent_time descending
        :rtype: QuerySet[Activity]
        :raises: Database errors propagate naturally (OperationalError, DatabaseError)
        
        Example:
            >>> recent = ActivityService.get_recent_activities(user, limit=10)
            >>> for activity in recent:
            ...     print(activity.name, activity.timestamp)
        """
        from django.db.models.functions import Coalesce, Greatest
        
        try:
            return Activity.objects.filter(
                workflow__playbook__author=user
            ).annotate(
                recent_time=Greatest(
                    Coalesce('last_accessed_at', 'updated_at'),
                    'updated_at'
                )
            ).select_related(
                'workflow', 'workflow__playbook'
            ).order_by('-recent_time')[:limit]
        except Exception as e:
            logger.error(f"Error fetching recent activities for user {user.username}: {e}")
            raise  # Propagate to caller for proper handling

    # ── Skill/Agent Link Management ────────────────────────────────────

    @staticmethod
    def set_activity_skill(activity_id: int, skill_id: int):
        """
        Link a skill to an activity. Both must belong to the same playbook.

        :param activity_id: Activity primary key
        :param skill_id: Skill primary key
        :returns: Updated Activity instance
        :raises Activity.DoesNotExist: If activity not found
        :raises Skill.DoesNotExist: If skill not found
        :raises ValidationError: If skill and activity are in different playbooks

        Example:
            >>> updated = ActivityService.set_activity_skill(1, 5)
            >>> updated.skill_id
            5
        """
        activity = Activity.objects.select_related('workflow__playbook').get(pk=activity_id)
        skill = Skill.objects.select_related('playbook').get(pk=skill_id)

        if activity.workflow.playbook_id != skill.playbook_id:
            raise ValidationError(
                f"Skill '{skill.title}' (playbook {skill.playbook_id}) and "
                f"activity '{activity.name}' (playbook {activity.workflow.playbook_id}) "
                f"must be in the same playbook"
            )

        activity.skill = skill
        activity.save(update_fields=['skill'])
        logger.info(
            "Linked skill %s '%s' to activity %s '%s'",
            skill_id, skill.title, activity_id, activity.name,
        )
        return activity

    @staticmethod
    def clear_activity_skill(activity_id: int):
        """
        Unlink skill from an activity (set FK to NULL).

        :param activity_id: Activity primary key
        :returns: Updated Activity instance
        :raises Activity.DoesNotExist: If activity not found

        Example:
            >>> updated = ActivityService.clear_activity_skill(1)
            >>> updated.skill_id is None
            True
        """
        activity = Activity.objects.get(pk=activity_id)
        old_skill_id = activity.skill_id
        activity.skill = None
        activity.save(update_fields=['skill'])
        logger.info(
            "Cleared skill (was %s) from activity %s '%s'",
            old_skill_id, activity_id, activity.name,
        )
        return activity

    @staticmethod
    def set_activity_agent(activity_id: int, agent_id: int):
        """
        Link an agent to an activity. Both must belong to the same playbook.

        :param activity_id: Activity primary key
        :param agent_id: Agent primary key
        :returns: Updated Activity instance
        :raises Activity.DoesNotExist: If activity not found
        :raises Agent.DoesNotExist: If agent not found
        :raises ValidationError: If agent and activity are in different playbooks

        Example:
            >>> updated = ActivityService.set_activity_agent(1, 3)
            >>> updated.agent_id
            3
        """
        activity = Activity.objects.select_related('workflow__playbook').get(pk=activity_id)
        agent = Agent.objects.select_related('playbook').get(pk=agent_id)

        if activity.workflow.playbook_id != agent.playbook_id:
            raise ValidationError(
                f"Agent '{agent.name}' (playbook {agent.playbook_id}) and "
                f"activity '{activity.name}' (playbook {activity.workflow.playbook_id}) "
                f"must be in the same playbook"
            )

        activity.agent = agent
        activity.save(update_fields=['agent'])
        logger.info(
            "Linked agent %s '%s' to activity %s '%s'",
            agent_id, agent.name, activity_id, activity.name,
        )
        return activity

    @staticmethod
    def clear_activity_agent(activity_id: int):
        """
        Unlink agent from an activity (set FK to NULL).

        :param activity_id: Activity primary key
        :returns: Updated Activity instance
        :raises Activity.DoesNotExist: If activity not found

        Example:
            >>> updated = ActivityService.clear_activity_agent(1)
            >>> updated.agent_id is None
            True
        """
        activity = Activity.objects.get(pk=activity_id)
        old_agent_id = activity.agent_id
        activity.agent = None
        activity.save(update_fields=['agent'])
        logger.info(
            "Cleared agent (was %s) from activity %s '%s'",
            old_agent_id, activity_id, activity.name,
        )
        return activity
    @staticmethod
    def set_activity_artifact_inputs(activity_id: int, artifact_ids: list[int]) -> int:
        """
        Set artifact inputs for activity (replaces existing).
        
        :param activity_id: Activity ID
        :param artifact_ids: List of artifact IDs to set as inputs
        :return: Number of artifact inputs created
        """
        from methodology.models import ArtifactInput
        
        # Clear existing
        ArtifactInput.objects.filter(activity_id=activity_id).delete()
        logger.info(f"Cleared existing artifact inputs for activity {activity_id}")
        
        # Create new
        count = 0
        for artifact_id in artifact_ids:
            ArtifactInput.objects.create(
                activity_id=activity_id,
                artifact_id=artifact_id,
                is_required=False
            )
            count += 1
            logger.info(f"Artifact {artifact_id} linked as input to activity {activity_id}")
        
        return count
