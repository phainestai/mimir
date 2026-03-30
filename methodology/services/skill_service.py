"""
Service layer for Skill operations.

Provides business logic for skill CRUD operations and validation.
Skills are step-by-step guidance documents attached 1:1 to Activities.
"""

import logging
from django.core.exceptions import ValidationError
from django.db.models import Q
from methodology.models import Skill

logger = logging.getLogger(__name__)


class SkillService:
    """Service class for skill operations."""

    @staticmethod
    def create_skill(activity, title, content=''):
        """
        Create a skill for an activity with validation.

        :param activity: Parent Activity instance
        :param title: Skill title (max 200 chars, required)
        :param content: Markdown content (optional)
        :returns: Created Skill instance
        :raises ValidationError: If title is empty or skill already exists for activity

        Example:
            >>> skill = SkillService.create_skill(
            ...     activity=act,
            ...     title='Setup React Component',
            ...     content='## Steps\\n1. Install deps\\n2. Create file'
            ... )
        """
        if not title or not title.strip():
            logger.warning(f"Skill creation failed: empty title for activity {activity.id}")
            raise ValidationError("Skill title cannot be empty")

        if len(title) > 200:
            logger.warning(f"Skill creation failed: title too long ({len(title)} chars)")
            raise ValidationError("Skill title cannot exceed 200 characters")

        if Skill.objects.filter(activity=activity).exists():
            logger.warning(f"Skill creation failed: skill already exists for activity {activity.id}")
            raise ValidationError(f"Activity '{activity.name}' already has a skill")

        skill = Skill.objects.create(
            activity=activity,
            title=title.strip(),
            content=content.strip() if content else ''
        )
        logger.info(f"Created skill '{skill.title}' (id={skill.id}) for activity {activity.id}")
        return skill

    @staticmethod
    def get_skill(skill_id):
        """
        Get a skill by ID with full select_related chain.

        :param skill_id: Skill primary key
        :returns: Skill instance
        :raises Skill.DoesNotExist: If skill not found

        Example:
            >>> skill = SkillService.get_skill(42)
        """
        return Skill.objects.select_related(
            'activity',
            'activity__workflow',
            'activity__workflow__playbook'
        ).get(pk=skill_id)

    @staticmethod
    def get_skill_for_activity(activity_id):
        """
        Get the skill for a given activity, or None if not yet created.

        :param activity_id: Activity primary key
        :returns: Skill instance or None
        :rtype: Skill | None

        Example:
            >>> skill = SkillService.get_skill_for_activity(7)
            >>> if skill is None:
            ...     print("No skill yet")
        """
        try:
            return Skill.objects.select_related(
                'activity',
                'activity__workflow',
                'activity__workflow__playbook'
            ).get(activity_id=activity_id)
        except Skill.DoesNotExist:
            return None

    @staticmethod
    def list_skills_for_playbook(playbook_id):
        """
        List all skills within a playbook.

        :param playbook_id: Playbook primary key
        :returns: QuerySet of Skill instances ordered by title
        :rtype: QuerySet[Skill]

        Example:
            >>> skills = SkillService.list_skills_for_playbook(1)
        """
        return Skill.objects.filter(
            activity__workflow__playbook_id=playbook_id
        ).select_related(
            'activity',
            'activity__workflow',
            'activity__workflow__playbook'
        ).order_by('title')

    @staticmethod
    def search_skills(query, user=None):
        """
        Search skills by title or content.

        :param query: Search string (case-insensitive, matches title or content)
        :param user: If provided, restrict to skills owned by this user
        :returns: QuerySet of matching Skill instances
        :rtype: QuerySet[Skill]

        Example:
            >>> results = SkillService.search_skills('react', user=maria)
        """
        qs = Skill.objects.select_related(
            'activity',
            'activity__workflow',
            'activity__workflow__playbook'
        )

        if user is not None:
            qs = qs.filter(
                activity__workflow__playbook__author=user,
                activity__workflow__playbook__source='owned'
            )

        if query:
            qs = qs.filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            )

        return qs.order_by('title')

    @staticmethod
    def update_skill(skill_id, **kwargs):
        """
        Update skill fields with validation.

        :param skill_id: Skill primary key
        :param kwargs: Fields to update (title, content)
        :returns: Updated Skill instance
        :raises ValidationError: If updated title is empty

        Example:
            >>> skill = SkillService.update_skill(42, title='New Title', content='New steps')
        """
        skill = Skill.objects.get(pk=skill_id)

        if 'title' in kwargs:
            new_title = kwargs['title']
            if not new_title or not new_title.strip():
                raise ValidationError("Skill title cannot be empty")
            if len(new_title) > 200:
                raise ValidationError("Skill title cannot exceed 200 characters")
            kwargs['title'] = new_title.strip()

        if 'content' in kwargs and kwargs['content']:
            kwargs['content'] = kwargs['content'].strip()

        for field, value in kwargs.items():
            setattr(skill, field, value)

        skill.save()
        logger.info(f"Updated skill {skill_id}: {', '.join(kwargs.keys())}")
        return skill

    @staticmethod
    def delete_skill(skill_id):
        """
        Delete a skill by ID.

        :param skill_id: Skill primary key
        :raises Skill.DoesNotExist: If skill not found

        Example:
            >>> SkillService.delete_skill(42)
        """
        skill = Skill.objects.get(pk=skill_id)
        title = skill.title
        activity_id = skill.activity_id
        skill.delete()
        logger.info(f"Deleted skill '{title}' (id={skill_id}) from activity {activity_id}")
