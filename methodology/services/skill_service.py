"""
Service layer for Skill operations.

Provides business logic for skill CRUD operations and validation.
Skills are playbook-scoped, reusable guides with capability_domain
and technology_stack metadata. Activities reference skills via nullable FK (1:N).
"""

import logging
from typing import Optional

from django.core.exceptions import ValidationError
from django.db.models import Count, Q, QuerySet

from methodology.models import Skill
from methodology.services.playbook_service import PlaybookService

logger = logging.getLogger(__name__)


class SkillService:
    """
    Service class for playbook-scoped skill operations.

    All methods are static — no instance state. Follows the repository
    pattern: validation + persistence + logging in one place.
    """

    # ── Constants ──────────────────────────────────────────────────────
    MAX_TITLE_LENGTH = 200
    MAX_DOMAIN_LENGTH = 100
    MAX_STACK_LENGTH = 100
    ALLOWED_UPDATE_FIELDS = {'title', 'content', 'capability_domain', 'technology_stack'}

    # ── Create ─────────────────────────────────────────────────────────

    @staticmethod
    def create_skill(
        playbook,
        title: str,
        content: str = '',
        capability_domain: str = '',
        technology_stack: str = '',
    ):
        """
        Create a skill within a playbook.

        :param playbook: Parent Playbook instance
        :param title: Skill title (max 200 chars, required)
        :param content: Markdown content (optional)
        :param capability_domain: What capability (e.g., "GUI_FORM") (optional)
        :param technology_stack: Technology used (e.g., "React+Redux") (optional)
        :returns: Created Skill instance
        :raises ValidationError: If title is empty or exceeds max length

        Example:
            >>> skill = SkillService.create_skill(
            ...     playbook=pb,
            ...     title='React Form Component',
            ...     capability_domain='GUI_FORM',
            ...     technology_stack='React+Redux',
            ...     content='## Steps\\n1. Install deps'
            ... )
        """
        SkillService._validate_title(title)
        SkillService._validate_metadata(capability_domain, technology_stack)

        skill = Skill.objects.create(
            playbook=playbook,
            title=title.strip(),
            content=content.strip() if content else '',
            capability_domain=capability_domain.strip() if capability_domain else '',
            technology_stack=technology_stack.strip() if technology_stack else '',
        )
        logger.info(
            "Created skill '%s' (id=%s) in playbook %s "
            "[domain=%s, stack=%s]",
            skill.title, skill.id, playbook.id,
            skill.capability_domain, skill.technology_stack,
        )
        return skill

    # ── Read ───────────────────────────────────────────────────────────

    @staticmethod
    def get_skill(skill_id: int):
        """
        Get a skill by ID with playbook prefetched.

        :param skill_id: Skill primary key
        :returns: Skill instance
        :raises Skill.DoesNotExist: If skill not found

        Example:
            >>> skill = SkillService.get_skill(42)
        """
        return Skill.objects.select_related('playbook').get(pk=skill_id)

    @staticmethod
    def get_skill_for_user(skill_id: int, user, *, write: bool = False):
        """Return skill if requesting user may view (or own for write) the parent playbook."""
        skill = Skill.objects.select_related("playbook").get(pk=skill_id)
        if write:
            PlaybookService.get_owned_playbook(skill.playbook_id, user)
        else:
            PlaybookService.get_playbook(skill.playbook_id, user)
        return skill

    @staticmethod
    def list_skills_for_playbook(
        playbook_id: int,
        capability_domain: str = '',
        technology_stack: str = '',
        search: str = '',
        unlinked_only: bool = False,
    ) -> QuerySet:
        """
        List skills in a playbook with optional filters.

        :param playbook_id: Playbook primary key
        :param capability_domain: Filter by exact domain match (optional)
        :param technology_stack: Filter by exact stack match (optional)
        :param search: Free-text search across title, domain, stack, content
        :param unlinked_only: If True, only skills with zero activity references
        :returns: QuerySet of Skill instances annotated with activity_count
        :rtype: QuerySet[Skill]

        Example:
            >>> skills = SkillService.list_skills_for_playbook(
            ...     1, capability_domain='GUI_FORM'
            ... )
        """
        qs = Skill.objects.filter(
            playbook_id=playbook_id
        ).select_related(
            'playbook'
        ).annotate(
            activity_count=Count('activities')
        )

        if capability_domain:
            qs = qs.filter(capability_domain=capability_domain)

        if technology_stack:
            qs = qs.filter(technology_stack=technology_stack)

        if search:
            qs = qs.filter(
                Q(title__icontains=search)
                | Q(capability_domain__icontains=search)
                | Q(technology_stack__icontains=search)
                | Q(content__icontains=search)
            )

        if unlinked_only:
            qs = qs.filter(activity_count=0)

        logger.info(
            "Listed skills for playbook %s [domain=%s, stack=%s, search=%s, unlinked=%s] -> %d results",
            playbook_id, capability_domain, technology_stack, search, unlinked_only, qs.count(),
        )
        return qs.order_by('title')

    @staticmethod
    def search_skills(query: str, user=None) -> QuerySet:
        """
        Search skills by title, content, capability_domain, or technology_stack.

        :param query: Search string (case-insensitive)
        :param user: If provided, restrict to skills in playbooks owned by this user
        :returns: QuerySet of matching Skill instances
        :rtype: QuerySet[Skill]

        Example:
            >>> results = SkillService.search_skills('react', user=maria)
        """
        qs = Skill.objects.select_related('playbook')

        if user is not None:
            qs = qs.filter(
                playbook__author=user,
                playbook__source='owned',
            )

        if query:
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(content__icontains=query)
                | Q(capability_domain__icontains=query)
                | Q(technology_stack__icontains=query)
            )

        return qs.order_by('title')

    @staticmethod
    def get_distinct_domains(playbook_id: int) -> list[str]:
        """
        Get distinct capability_domain values for autocomplete.

        :param playbook_id: Playbook primary key
        :returns: Sorted list of unique non-empty domain values
        :rtype: list[str]

        Example:
            >>> SkillService.get_distinct_domains(1)
            ['API_CRUD', 'DB_MIGRATION', 'GUI_FORM']
        """
        return sorted(
            Skill.objects.filter(playbook_id=playbook_id)
            .exclude(capability_domain='')
            .values_list('capability_domain', flat=True)
            .distinct()
        )

    @staticmethod
    def get_distinct_stacks(playbook_id: int) -> list[str]:
        """
        Get distinct technology_stack values for autocomplete.

        :param playbook_id: Playbook primary key
        :returns: Sorted list of unique non-empty stack values
        :rtype: list[str]

        Example:
            >>> SkillService.get_distinct_stacks(1)
            ['Django+HTMX', 'FastAPI', 'React+Redux']
        """
        return sorted(
            Skill.objects.filter(playbook_id=playbook_id)
            .exclude(technology_stack='')
            .values_list('technology_stack', flat=True)
            .distinct()
        )

    # ── Update ─────────────────────────────────────────────────────────

    @staticmethod
    def update_skill(skill_id: int, **kwargs):
        """
        Update skill fields with validation.

        :param skill_id: Skill primary key
        :param kwargs: Fields to update (title, content, capability_domain, technology_stack)
        :returns: Updated Skill instance
        :raises ValidationError: If title is empty or fields are invalid
        :raises Skill.DoesNotExist: If skill not found

        Example:
            >>> skill = SkillService.update_skill(
            ...     42, title='New Title', capability_domain='API_CRUD'
            ... )
        """
        skill = Skill.objects.get(pk=skill_id)

        SkillService._validate_update_fields(kwargs)

        if 'title' in kwargs:
            SkillService._validate_title(kwargs['title'])
            kwargs['title'] = kwargs['title'].strip()

        if 'capability_domain' in kwargs:
            kwargs['capability_domain'] = kwargs['capability_domain'].strip() if kwargs['capability_domain'] else ''

        if 'technology_stack' in kwargs:
            kwargs['technology_stack'] = kwargs['technology_stack'].strip() if kwargs['technology_stack'] else ''

        if 'content' in kwargs:
            kwargs['content'] = kwargs['content'].strip() if kwargs['content'] else ''

        for field, value in kwargs.items():
            setattr(skill, field, value)

        skill.save()
        logger.info("Updated skill %s: %s", skill_id, ', '.join(kwargs.keys()))
        return skill

    # ── Delete ─────────────────────────────────────────────────────────

    @staticmethod
    def delete_skill(skill_id: int) -> None:
        """
        Delete a skill by ID. M2M links to activities are cleared automatically.

        :param skill_id: Skill primary key
        :raises Skill.DoesNotExist: If skill not found

        Example:
            >>> SkillService.delete_skill(42)
        """
        skill = Skill.objects.get(pk=skill_id)
        title = skill.title
        playbook_id = skill.playbook_id
        activity_count = skill.activities.count()

        skill.delete()
        logger.info(
            "Deleted skill '%s' (id=%s) from playbook %s "
            "[%d activities had references cleared]",
            title, skill_id, playbook_id, activity_count,
        )

    # ── Activity Queries + Facades ───────────────────────────────────

    @staticmethod
    def get_activities_for_skill(skill_id: int):
        """
        Get all activities referencing a given skill.

        :param skill_id: Skill primary key
        :returns: QuerySet of Activity instances ordered by workflow name, activity name
        :rtype: QuerySet[Activity]

        Example:
            >>> activities = SkillService.get_activities_for_skill(42)
            >>> [a.name for a in activities]
            ['Build Login Form', 'Build Settings Form']
        """
        from methodology.models import Activity
        qs = Activity.objects.filter(
            skills__id=skill_id
        ).select_related('workflow').order_by('workflow__name', 'name').distinct()
        logger.info("Fetched %d activities for skill %s", qs.count(), skill_id)
        return qs

    @staticmethod
    def link_skill_to_activity(activity_id: int, skill_id: int):
        """
        Facade: add a skill to an activity. Delegates to ActivityService.

        :param activity_id: Activity primary key
        :param skill_id: Skill primary key
        :returns: Updated Activity instance
        """
        from methodology.services.activity_service import ActivityService
        return ActivityService.add_activity_skill(activity_id, skill_id)

    @staticmethod
    def unlink_skill_from_activity(activity_id: int, skill_id: int):
        """
        Facade: remove a skill from an activity. Delegates to ActivityService.

        :param activity_id: Activity primary key
        :param skill_id: Skill primary key
        :returns: Updated Activity instance
        """
        from methodology.services.activity_service import ActivityService
        return ActivityService.remove_activity_skill(activity_id, skill_id)

    # ── Private validation helpers ─────────────────────────────────────

    @staticmethod
    def _validate_title(title: str) -> None:
        """
        Validate skill title: non-empty, within max length.

        :param title: Title string to validate
        :raises ValidationError: If title is empty or too long
        """
        if not title or not title.strip():
            raise ValidationError("Skill title cannot be empty")
        if len(title) > SkillService.MAX_TITLE_LENGTH:
            raise ValidationError(
                f"Skill title cannot exceed {SkillService.MAX_TITLE_LENGTH} characters"
            )

    @staticmethod
    def _validate_metadata(
        capability_domain: str, technology_stack: str
    ) -> None:
        """
        Validate optional metadata field lengths.

        :param capability_domain: Domain value to check
        :param technology_stack: Stack value to check
        :raises ValidationError: If either exceeds max length
        """
        if capability_domain and len(capability_domain) > SkillService.MAX_DOMAIN_LENGTH:
            raise ValidationError(
                f"Capability domain cannot exceed {SkillService.MAX_DOMAIN_LENGTH} characters"
            )
        if technology_stack and len(technology_stack) > SkillService.MAX_STACK_LENGTH:
            raise ValidationError(
                f"Technology stack cannot exceed {SkillService.MAX_STACK_LENGTH} characters"
            )

    @staticmethod
    def _validate_update_fields(kwargs: dict) -> None:
        """
        Ensure only allowed fields are being updated.

        :param kwargs: Fields dict to validate
        :raises ValidationError: If unknown fields are provided
        """
        unknown = set(kwargs.keys()) - SkillService.ALLOWED_UPDATE_FIELDS
        if unknown:
            raise ValidationError(f"Cannot update fields: {unknown}")
