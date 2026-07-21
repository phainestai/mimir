"""
Integration tests for get_playbook version history extensions.

Covers FOB-MCP-VH-01 (include_history), FOB-MCP-VH-02 (version snapshot),
FOB-MCP-VH-03 (not-found guard).

Uses real DB and real PlaybookVersion rows — no mocking.
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model

from methodology.models import Playbook, PlaybookVersion, VersionSource
from methodology.services.playbook_service import PlaybookService
from mcp_integration.context import set_current_user
from mcp_integration.tools import get_playbook

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_user(db):
    return User.objects.create_user(username="vh_admin", password="pass", is_staff=True)


@pytest.fixture
def released_playbook(db, admin_user):
    """A released playbook — service auto-creates PlaybookVersion v1.0 row."""
    return PlaybookService.create_playbook(
        name="VH Test Playbook",
        description="Version history integration test",
        category="development",
        author=admin_user,
        status="released",
    )


@pytest.fixture
def released_playbook_with_extra_versions(db, released_playbook, admin_user):
    """Adds a second PlaybookVersion row to give us two history entries."""
    PlaybookVersion.objects.create(
        playbook=released_playbook,
        version_number=Decimal("2.0"),
        snapshot_data={"name": released_playbook.name, "version": "2.0", "workflows": []},
        change_summary="Second major release",
        description="Second major release",
        is_major=True,
        source=VersionSource.PIP_SOURCE,
        created_by=admin_user,
    )
    released_playbook.version = Decimal("2.0")
    released_playbook.save()
    return released_playbook


@pytest.fixture
def draft_playbook(db, admin_user):
    """A draft playbook — no PlaybookVersion rows created automatically."""
    return PlaybookService.create_playbook(
        name="VH Draft Playbook",
        description="Draft — no version rows",
        category="development",
        author=admin_user,
        status="draft",
    )


@pytest.fixture
def mcp_context(admin_user):
    set_current_user(admin_user)
    return admin_user


# ---------------------------------------------------------------------------
# S1: FOB-MCP-VH-01 — include_history=True
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
class TestGetPlaybookIncludeHistory:

    @pytest.mark.asyncio
    async def test_default_call_has_no_versions_key(self, mcp_context, released_playbook):
        """Default get_playbook must not include a 'versions' key (lean response)."""
        result = await get_playbook(playbook_id=released_playbook.id)
        assert "versions" not in result

    @pytest.mark.asyncio
    async def test_include_history_true_returns_versions_list(
        self, mcp_context, released_playbook_with_extra_versions
    ):
        """include_history=True adds 'versions' list with correct keys."""
        pb = released_playbook_with_extra_versions
        result = await get_playbook(playbook_id=pb.id, include_history=True)

        assert "versions" in result
        versions = result["versions"]
        assert isinstance(versions, list)
        assert len(versions) >= 1

        entry = versions[0]
        for key in ("version_number", "source", "pip_id", "change_summary", "created_at", "is_major"):
            assert key in entry, f"Missing key '{key}' in version entry"

    @pytest.mark.asyncio
    async def test_include_history_versions_ordered_newest_first(
        self, mcp_context, released_playbook_with_extra_versions
    ):
        """Versions must be ordered newest (highest version_number) first."""
        pb = released_playbook_with_extra_versions
        result = await get_playbook(playbook_id=pb.id, include_history=True)
        versions = result["versions"]
        assert len(versions) == 2
        assert versions[0]["version_number"] == "2.0"
        assert versions[1]["version_number"] == "1.0"

    @pytest.mark.asyncio
    async def test_include_history_standard_fields_still_present(
        self, mcp_context, released_playbook
    ):
        """include_history=True must not drop the standard playbook fields."""
        result = await get_playbook(playbook_id=released_playbook.id, include_history=True)
        for key in ("id", "name", "status", "version", "workflows"):
            assert key in result, f"Standard field '{key}' missing when include_history=True"

    @pytest.mark.asyncio
    async def test_include_history_empty_list_when_no_versions(
        self, mcp_context, draft_playbook
    ):
        """Draft with no PlaybookVersion rows → versions: []."""
        result = await get_playbook(playbook_id=draft_playbook.id, include_history=True)
        assert result["versions"] == []


# ---------------------------------------------------------------------------
# S2: FOB-MCP-VH-02 — version snapshot
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
class TestGetPlaybookVersionSnapshot:

    @pytest.mark.asyncio
    async def test_version_param_returns_snapshot_data(
        self, mcp_context, released_playbook_with_extra_versions
    ):
        """version='1.0' returns snapshot_data and metadata for that version."""
        pb = released_playbook_with_extra_versions
        result = await get_playbook(playbook_id=pb.id, version="1.0")

        assert "snapshot_data" in result
        assert result["snapshot_data"] is not None
        assert result["version_number"] == "1.0"
        assert result["is_major"] is True

    @pytest.mark.asyncio
    async def test_version_response_contains_required_keys(
        self, mcp_context, released_playbook_with_extra_versions
    ):
        """Snapshot response includes all required metadata keys."""
        pb = released_playbook_with_extra_versions
        result = await get_playbook(playbook_id=pb.id, version="2.0")

        for key in ("version_number", "source", "pip_id", "change_summary", "created_at", "is_major", "snapshot_data"):
            assert key in result, f"Missing key '{key}' in snapshot response"

    @pytest.mark.asyncio
    async def test_version_snapshot_does_not_include_workflows_list(
        self, mcp_context, released_playbook_with_extra_versions
    ):
        """When version= is provided, response is the snapshot only (no top-level workflows key)."""
        pb = released_playbook_with_extra_versions
        result = await get_playbook(playbook_id=pb.id, version="1.0")
        assert "workflows" not in result

    @pytest.mark.asyncio
    async def test_version_takes_precedence_over_include_history(
        self, mcp_context, released_playbook_with_extra_versions
    ):
        """When both version and include_history are set, version takes precedence (snapshot only)."""
        pb = released_playbook_with_extra_versions
        result = await get_playbook(playbook_id=pb.id, version="1.0", include_history=True)
        assert "snapshot_data" in result
        assert "versions" not in result


# ---------------------------------------------------------------------------
# S3: FOB-MCP-VH-03 — not-found guard
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
class TestGetPlaybookVersionNotFound:

    @pytest.mark.asyncio
    async def test_unknown_version_raises_value_error(
        self, mcp_context, released_playbook
    ):
        """version='99.9' raises ValueError with the version number in the message."""
        with pytest.raises(ValueError) as exc_info:
            await get_playbook(playbook_id=released_playbook.id, version="99.9")
        assert "99.9" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unknown_version_error_mentions_playbook(
        self, mcp_context, released_playbook
    ):
        """ValueError message must also reference the playbook id."""
        with pytest.raises(ValueError) as exc_info:
            await get_playbook(playbook_id=released_playbook.id, version="99.9")
        assert str(released_playbook.id) in str(exc_info.value)
