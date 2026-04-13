"""
Unit tests for PhaseService.

Tests cover: create, list, get by id/name, update, delete (with activity
unassignment and reorder), reorder, and the string-phase migration helper.
"""

import pytest
from django.test import TestCase

from methodology.models import Phase
from methodology.services.phase_service import PhaseService


class TestPhaseServiceCreate(TestCase):
    """PhaseService.create_phase"""

    def test_create_phase_success(self):
        """Create a phase with name+description; order auto-assigned to 1."""
        raise NotImplementedError()

    def test_create_phase_auto_order_increments(self):
        """Second phase gets order=2 when no explicit order given."""
        raise NotImplementedError()

    def test_create_phase_explicit_order(self):
        """Explicit order is respected."""
        raise NotImplementedError()

    def test_create_phase_strips_whitespace(self):
        """Leading/trailing whitespace stripped from name."""
        raise NotImplementedError()

    def test_create_phase_empty_name_raises(self):
        """Blank name raises ValidationError."""
        raise NotImplementedError()

    def test_create_phase_duplicate_name_raises(self):
        """Duplicate name within same workflow raises ValidationError."""
        raise NotImplementedError()

    def test_create_phase_same_name_different_workflow_ok(self):
        """Same name in different workflow is allowed."""
        raise NotImplementedError()


class TestPhaseServiceGet(TestCase):
    """PhaseService.get_phases_for_workflow / get_phase_by_id / get_phase_by_name"""

    def test_get_phases_for_workflow_ordered(self):
        """Returns phases ordered by order asc."""
        raise NotImplementedError()

    def test_get_phases_for_workflow_empty(self):
        """Returns empty queryset when workflow has no phases."""
        raise NotImplementedError()

    def test_get_phase_by_id_found(self):
        """Returns phase when id exists."""
        raise NotImplementedError()

    def test_get_phase_by_id_not_found_raises(self):
        """Raises ValueError for non-existent id."""
        raise NotImplementedError()

    def test_get_phase_by_name_case_insensitive(self):
        """Name lookup is case-insensitive."""
        raise NotImplementedError()

    def test_get_phase_by_name_not_found_returns_none(self):
        """Returns None when name does not exist."""
        raise NotImplementedError()


class TestPhaseServiceUpdate(TestCase):
    """PhaseService.update_phase"""

    def test_update_name(self):
        """Name update persisted correctly."""
        raise NotImplementedError()

    def test_update_description(self):
        """Description update persisted correctly."""
        raise NotImplementedError()

    def test_update_order(self):
        """Order update persisted correctly."""
        raise NotImplementedError()

    def test_update_duplicate_name_raises(self):
        """Changing name to an existing phase name raises ValidationError."""
        raise NotImplementedError()


class TestPhaseServiceDelete(TestCase):
    """PhaseService.delete_phase"""

    def test_delete_phase_removes_it(self):
        """Phase is deleted from DB."""
        raise NotImplementedError()

    def test_delete_phase_unassigns_activities(self):
        """Activities that belonged to the phase have phase_fk=None after deletion."""
        raise NotImplementedError()

    def test_delete_phase_renumbers_remaining(self):
        """Remaining phases are renumbered contiguously from 1."""
        raise NotImplementedError()


class TestPhaseServiceReorder(TestCase):
    """PhaseService.reorder_phases"""

    def test_reorder_phases_success(self):
        """Phases get new order values matching the provided id sequence."""
        raise NotImplementedError()

    def test_reorder_phases_foreign_id_raises(self):
        """ID belonging to a different workflow raises ValueError."""
        raise NotImplementedError()


class TestPhaseServiceMigration(TestCase):
    """PhaseService.migrate_string_phases"""

    def test_migration_creates_phases_from_strings(self):
        """Unique phase strings become Phase records."""
        raise NotImplementedError()

    def test_migration_links_activities_to_phases(self):
        """Activity.phase_fk is set after migration."""
        raise NotImplementedError()

    def test_migration_is_idempotent(self):
        """Running twice does not create duplicate phases."""
        raise NotImplementedError()

    def test_migration_skips_blank_phase_strings(self):
        """Activities with blank phase string get phase_fk=None."""
        raise NotImplementedError()
