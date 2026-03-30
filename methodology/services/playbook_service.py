"""
Playbook Service - Business logic for playbook operations.

Generic service layer used by both UI views and MCP tools.
"""

import logging
from decimal import Decimal
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from methodology.models import Playbook, PlaybookVersion

logger = logging.getLogger(__name__)


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
                    version_number=1,
                    snapshot_data={'name': playbook.name, 'version': str(playbook.version)},
                    change_summary='Initial version',
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
    def release_playbook(playbook_id, author):
        """
        Release draft playbook to production (version 1.0).
        
        Transitions from draft (0.x) to released (1.0).
        After release, playbook requires PIP workflow for changes.
        
        :param playbook_id: Playbook ID
        :param author: User instance (must be owner)
        :returns: Released Playbook instance
        :raises ValidationError: If not draft or other validation fails
        :raises PermissionError: If user doesn't own playbook
        
        Example:
            >>> playbook = PlaybookService.release_playbook(
            ...     playbook_id=1,
            ...     author=user
            ... )
            >>> playbook.version
            Decimal('1.0')
            >>> playbook.status
            'released'
        """
        logger.info(f"Releasing playbook id={playbook_id}, author={author.id}")
        
        playbook = Playbook.objects.get(pk=playbook_id)
        
        # Permission check
        if playbook.author != author:
            logger.error(f"User {author.id} attempted to release playbook {playbook_id} owned by {playbook.author.id}")
            raise PermissionError("You don't have permission to release this playbook")
        
        # Validation - must be draft
        if not playbook.is_draft:
            logger.error(f"Attempted to release non-draft playbook {playbook_id} (status={playbook.status})")
            raise ValidationError(f"Only draft playbooks can be released. Current status: {playbook.status}")
        
        old_version = playbook.version
        old_status = playbook.status
        
        # Call model method and persist
        playbook.release()
        playbook.save()
        
        logger.info(f"Playbook '{playbook.name}' released: {old_status} v{old_version} → {playbook.status} v{playbook.version}")
        return playbook
