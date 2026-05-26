"""
Playbook Service - Business logic for playbook operations.

Generic service layer used by both UI views and MCP tools.
"""

import logging
from decimal import Decimal
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from methodology.models import Playbook, PlaybookVersion, VersionSource, Workflow

logger = logging.getLogger(__name__)

_PLAYBOOK_VISIBILITY_ALLOWED = frozenset({"private", "public"})


def _validate_playbook_visibility(visibility: str) -> None:
    """Raise ValidationError if visibility is not allowed for GUI/MCP creates and updates."""
    if visibility not in _PLAYBOOK_VISIBILITY_ALLOWED:
        logger.warning("Rejected playbook visibility value %r (allowed=%s)", visibility, _PLAYBOOK_VISIBILITY_ALLOWED)
        raise ValidationError("Visibility must be private or public.")


def _playbook_release_snapshot(playbook: Playbook) -> dict:
    """JSON-serializable snapshot of playbook structure for PlaybookVersion."""
    workflows = Workflow.objects.filter(playbook=playbook).order_by("order", "created_at")
    return {
        "name": playbook.name,
        "description": playbook.description,
        "category": playbook.category,
        "status": playbook.status,
        "version": str(playbook.version),
        "workflows": [
            {"id": w.pk, "name": w.name, "order": w.order, "abbreviation": w.abbreviation}
            for w in workflows
        ],
    }


class PlaybookService:
    """Service class for playbook CRUD operations."""

    @staticmethod
    def create_playbook(name, description, category, author, 
                       status='draft', visibility='private', source='owned'):
        """
        Create playbook with validation.
        
        Used by both UI and MCP.
        
        :param name: Playbook name (max 100 chars, unique per author)
        :param description: Description (max 500 chars)
        :param category: Category (product/development/research/design/other)
        :param author: User instance
        :param status: draft/active/released/disabled (default: draft)
        :param visibility: private or public (default: private)
        :param source: owned/downloaded (default: owned)
        :returns: Created Playbook instance
        :raises ValidationError: If validation fails
        
        Example:
            >>> playbook = PlaybookService.create_playbook(
            ...     name="React Development",
            ...     description="Modern React patterns",
            ...     category="development",
            ...     author=user
            ... )
        """
        logger.info(f"Creating playbook '{name}' for author {author.id}, status={status}")
        
        # Validate name
        if not name or not name.strip():
            logger.warning(f"Playbook creation failed: empty name")
            raise ValidationError("Playbook name cannot be empty")

        _validate_playbook_visibility(visibility)

        # Set initial version based on status
        initial_version = Decimal('1.0') if status in ['released', 'active'] else Decimal('0.1')
        
        try:
            playbook = Playbook.objects.create(
                name=name.strip(),
                description=description.strip() if description else '',
                category=category,
                author=author,
                status=status,
                version=initial_version,
                visibility=visibility,
                source=source
            )
            
            # Create initial version record for non-draft playbooks (active and released both
            # start at version 1.0 and need an audit trail entry from day one).
            if status in ['released', 'active']:
                PlaybookVersion.objects.create(
                    playbook=playbook,
                    version_number=Decimal('1.0'),
                    snapshot_data={'name': playbook.name, 'version': str(playbook.version)},
                    change_summary='Initial version',
                    description='Initial version',
                    is_major=True,
                    source=VersionSource.RELEASE,
                    created_by=author,
                )
            
            logger.info(f"Created playbook '{name}' (id={playbook.id}, version={playbook.version})")
            return playbook
            
        except IntegrityError as e:
            logger.error(f"Playbook creation failed: duplicate name '{name}' for author {author.id}")
            raise ValidationError(f"Playbook '{name}' already exists") from e
    
    @staticmethod
    def get_playbook(playbook_id, user, *, prefetch_workflows: bool = False):
        """
        Get playbook by ID if ``user`` may view it (owner or public non-draft per ``can_view``).

        :param playbook_id: Playbook ID
        :param user: Requesting Django user
        :param prefetch_workflows: When True, prefetch ``workflows`` for list/detail responses
        :returns: Playbook instance
        :raises Playbook.DoesNotExist: If playbook row is missing
        :raises PermissionError: If user may not view this playbook (treated as not found by MCP)
        """
        qs = Playbook.objects
        if prefetch_workflows:
            qs = qs.prefetch_related("workflows")
        logger.info(
            "Retrieving playbook id=%s for user id=%s (prefetch_workflows=%s)",
            playbook_id,
            getattr(user, "pk", user),
            prefetch_workflows,
        )
        try:
            playbook = qs.get(pk=playbook_id)
        except Playbook.DoesNotExist:
            logger.info("Playbook id=%s not found", playbook_id)
            raise
        if not playbook.can_view(user):
            logger.info(
                "User id=%s denied view on playbook id=%s (visibility=%s)",
                getattr(user, "pk", user),
                playbook_id,
                playbook.visibility,
            )
            raise PermissionError(f"Playbook {playbook_id} not found")
        return playbook

    @staticmethod
    def get_owned_playbook(playbook_id, user):
        """
        Return playbook only if ``user`` is the author (for mutating operations).

        :param playbook_id: Playbook primary key
        :param user: Django user
        :returns: Playbook instance
        :raises Playbook.DoesNotExist: If missing or not owned by user
        """
        try:
            playbook = Playbook.objects.get(pk=playbook_id, author=user)
        except Playbook.DoesNotExist:
            logger.info(
                "get_owned_playbook: playbook id=%s not found for user id=%s",
                playbook_id,
                getattr(user, "pk", user),
            )
            raise Playbook.DoesNotExist(
                f"Playbook with id={playbook_id} does not exist."
            ) from None
        return playbook
    
    @staticmethod
    def list_playbooks(author, status=None):
        """
        List playbooks for author, optionally filtered by status.
        
        :param author: User instance
        :param status: Optional status filter (draft/released/active/disabled)
        :returns: QuerySet of Playbook instances
        
        Example:
            >>> draft_playbooks = PlaybookService.list_playbooks(user, status='draft')
        """
        logger.info(f"Listing playbooks for author {author.id}, status_filter={status}")
        
        queryset = Playbook.objects.filter(author=author)
        if status:
            queryset = queryset.filter(status=status)
        
        playbooks = list(queryset)
        logger.info(f"Found {len(playbooks)} playbooks")
        return playbooks

    @staticmethod
    def list_public_playbooks(exclude_author):
        """
        Public, non-draft playbooks authored by other users (FOB browse list).

        Draft playbooks stay owner-only even when visibility is Public.

        :param exclude_author: Current user; their own playbooks appear in the owned list.
        :returns: List of Playbook instances, newest first
        """
        qs = (
            Playbook.objects.filter(visibility="public")
            .exclude(status="draft")
            .exclude(author=exclude_author)
            .select_related("author")
            .order_by("-updated_at")
        )
        rows = list(qs)
        logger.info(
            "Listed %s public playbooks for user id=%s (excluding own and draft)",
            len(rows),
            getattr(exclude_author, "pk", exclude_author),
        )
        return rows

    @staticmethod
    def list_team_playbooks_for_user(user):
        """
        Released playbooks shared via team membership (excludes own-authored).

        :param user: User whose team playbooks to retrieve.
        :returns: List of Playbook instances accessible via teams.
        """
        from methodology.models import TeamMembership, TeamPlaybook
        
        logger.info(f"Listing team playbooks for user {user.id}")
        
        # Get all teams where user is a member
        team_ids = TeamMembership.objects.filter(user=user).values_list("team_id", flat=True)
        
        # Get all playbooks linked to those teams (excluding own-authored)
        playbook_ids = TeamPlaybook.objects.filter(team_id__in=team_ids).values_list("playbook_id", flat=True)
        
        qs = (
            Playbook.objects.filter(pk__in=playbook_ids)
            .exclude(author=user)
            .select_related("author")
            .order_by("-updated_at")
        )
        rows = list(qs)
        logger.info(f"Found {len(rows)} team playbooks for user {user.id}")
        return rows

    @staticmethod
    def get_accessible_playbook_ids(user):
        """
        Get IDs of all playbooks accessible to user (owned + public + team).
        
        Useful for filtering related objects (workflows, activities, etc.) to only
        show items from playbooks the user can access.
        
        :param user: User whose accessible playbooks to retrieve.
        :returns: Set of playbook IDs.
        """
        from methodology.models import TeamMembership, TeamPlaybook
        
        logger.info(f"Getting accessible playbook IDs for user {user.id}")
        
        # Get owned playbook IDs
        owned_ids = set(
            Playbook.objects.filter(author=user).values_list('id', flat=True)
        )
        
        # Get public playbook IDs (non-draft, excluding own)
        public_ids = set(
            Playbook.objects.filter(visibility="public", status="released")
            .exclude(author=user)
            .values_list('id', flat=True)
        )
        
        # Get team playbook IDs
        team_ids = list(TeamMembership.objects.filter(user=user).values_list("team_id", flat=True))
        team_playbook_ids = set(
            TeamPlaybook.objects.filter(team_id__in=team_ids).values_list("playbook_id", flat=True)
        )
        
        # Combine all IDs
        all_ids = owned_ids | public_ids | team_playbook_ids
        
        logger.info(
            f"User {user.id} has access to {len(all_ids)} playbooks "
            f"({len(owned_ids)} owned, {len(public_ids)} public, {len(team_playbook_ids)} team)"
        )
        return all_ids

    @staticmethod
    @transaction.atomic
    def update_playbook(playbook_id, **data):
        """
        Update playbook fields with validation.
        
        :param playbook_id: Playbook ID
        :param data: Fields to update (name, description, category, etc.)
        :returns: Updated Playbook instance
        :raises ValidationError: If validation fails
        
        Example:
            >>> playbook = PlaybookService.update_playbook(
            ...     playbook_id=1,
            ...     name="New Name",
            ...     description="Updated description"
            ... )
        """
        logger.info(f"Updating playbook {playbook_id}")
        
        playbook = Playbook.objects.get(pk=playbook_id)

        if "visibility" in data:
            _validate_playbook_visibility(data["visibility"])

        # Check for duplicate name if changing name
        if 'name' in data and data['name'] != playbook.name:
            if Playbook.objects.filter(author=playbook.author, name=data['name']).exists():
                logger.warning(f"Playbook update failed: duplicate name '{data['name']}'")
                raise ValidationError(f"Playbook '{data['name']}' already exists")
        
        # Update fields
        for field, value in data.items():
            if hasattr(playbook, field):
                setattr(playbook, field, value)
        
        playbook.save()
        logger.info(f"Playbook {playbook_id} updated")
        return playbook
    
    @staticmethod
    @transaction.atomic
    def delete_playbook(playbook_id):
        """
        Delete playbook (cascades to workflows and activities).
        
        :param playbook_id: Playbook ID
        
        Example:
            >>> PlaybookService.delete_playbook(1)
        """
        logger.info(f"Deleting playbook {playbook_id}")
        playbook = Playbook.objects.get(pk=playbook_id)
        playbook_name = playbook.name
        playbook.delete()
        logger.info(f"Playbook '{playbook_name}' (id={playbook_id}) deleted")
    
    @staticmethod
    @transaction.atomic
    def duplicate_playbook(playbook_id, new_name, author):
        """
        Duplicate playbook (deep copy with workflows and activities).
        
        :param playbook_id: Original playbook ID
        :param new_name: Name for duplicate
        :param author: User instance (owner of duplicate)
        :returns: Duplicated Playbook instance
        :raises ValidationError: If new name already exists
        
        Example:
            >>> duplicate = PlaybookService.duplicate_playbook(
            ...     playbook_id=1,
            ...     new_name="My Copy",
            ...     author=user
            ... )
        """
        logger.info(f"Duplicating playbook {playbook_id} as '{new_name}'")
        
        original = Playbook.objects.get(pk=playbook_id)
        
        # Check for duplicate name
        if Playbook.objects.filter(author=author, name=new_name).exists():
            logger.warning(f"Duplicate failed: name '{new_name}' already exists")
            raise ValidationError(f"Playbook '{new_name}' already exists")
        
        # Create duplicate (workflows/activities handled by UI views currently)
        duplicate = Playbook.objects.create(
            name=new_name,
            description=original.description,
            category=original.category,
            author=author,
            status='draft',  # Always start as draft
            version=Decimal('0.1'),  # Reset version
            visibility=original.visibility,
            source='owned'
        )
        
        logger.info(f"Playbook duplicated as {duplicate.pk}")
        return duplicate
    
    @staticmethod
    @transaction.atomic
    def release_playbook(playbook_id, author, *, description: str):
        """
        Publish a draft playbook to released, or bump a released playbook to the next major line.

        Requires a non-empty release description and at least one workflow (VERSIONING-18).

        Draft 0.x transitions to ``released`` at the next major line (for example 0.9 → 1.0).
        Released ``1.x`` bumps to the next major (for example 1.3 → 2.0) while staying released.

        :param playbook_id: Playbook PK
        :param author: Acting user (must own the playbook)
        :param description: Release notes (non-empty)
        :raises ValidationError: invalid state, empty description, or no workflows
        :raises PermissionError: not the owner
        """
        description_clean = (description or "").strip()
        if not description_clean:
            raise ValidationError(
                {"release_description": "Release description is required."},
                code="release_description_required",
            )

        playbook = Playbook.objects.get(pk=playbook_id)

        if playbook.author != author:
            logger.error(
                "User %s attempted release on playbook %s owned by %s",
                author.id,
                playbook_id,
                playbook.author_id,
            )
            raise PermissionError("You don't have permission to release this playbook")

        if playbook.status not in ("draft", "released"):
            raise ValidationError(
                f"Release is only available for draft or released playbooks "
                f"(current status: {playbook.status})"
            )

        if not Workflow.objects.filter(playbook=playbook).exists():
            raise ValidationError(
                "Add at least one workflow before releasing this playbook.",
                code="release_requires_workflow",
            )

        was_draft = playbook.status == "draft"
        next_version = playbook.compute_next_major_line_version()
        snapshot_before = _playbook_release_snapshot(playbook)

        if was_draft:
            playbook.status = "released"
        playbook.version = next_version
        update_fields = ["version", "updated_at"]
        if was_draft:
            update_fields.insert(0, "status")
        playbook.save(update_fields=update_fields)

        playbook.refresh_from_db()
        snapshot_after = _playbook_release_snapshot(playbook)

        PlaybookVersion.objects.create(
            playbook=playbook,
            version_number=next_version,
            snapshot_data={**snapshot_after, "before_release": snapshot_before},
            change_summary=description_clean,
            description=description_clean,
            is_major=True,
            source=VersionSource.RELEASE,
            created_by=author,
        )

        logger.info(
            "Playbook '%s' (id=%s) advanced to released major v%s",
            playbook.name,
            playbook.pk,
            next_version,
        )
        return playbook

    @staticmethod
    @transaction.atomic
    def revert_released_playbook_to_draft(
        playbook_id, *, actor, reason: str
    ) -> Playbook:
        """
        Staff transition: ``released`` → ``draft``, keeping the current playbook version.

        When no ``PlaybookVersion`` row exists yet for ``playbook.version``, inserts an
        admin-sourced audit row (unique constraint is per ``(playbook, version_number)``).
        """
        text = (reason or "").strip()
        if not text:
            raise ValidationError("Revert reason is required.")

        if not getattr(actor, "is_staff", False):
            raise PermissionError("Only staff can revert a released playbook to draft.")

        playbook = Playbook.objects.get(pk=playbook_id)
        if playbook.status != "released":
            raise ValidationError(
                "Only released playbooks can be reverted to draft "
                f"(current status: {playbook.status})."
            )

        hold_version = playbook.version
        playbook.status = "draft"
        playbook.save(update_fields=["status", "updated_at"])

        if not PlaybookVersion.objects.filter(
            playbook=playbook, version_number=hold_version
        ).exists():
            PlaybookVersion.objects.create(
                playbook=playbook,
                version_number=hold_version,
                snapshot_data={
                    "event": "admin_revert_to_draft",
                    "version": str(hold_version),
                    "name": playbook.name,
                },
                change_summary=text,
                description=text,
                is_major=False,
                source=VersionSource.ADMIN,
                created_by=actor,
            )

        logger.info(
            "Playbook id=%s reverted released → draft at v%s",
            playbook_id,
            hold_version,
        )
        return playbook
