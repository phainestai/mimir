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
        :param visibility: private/family/local (default: private)
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
    def get_playbook(playbook_id):
        """
        Get playbook by ID.
        
        :param playbook_id: Playbook ID
        :returns: Playbook instance
        :raises Playbook.DoesNotExist: If not found
        """
        logger.info(f"Retrieving playbook {playbook_id}")
        return Playbook.objects.get(pk=playbook_id)
    
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
