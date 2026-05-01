"""S03 release flow skeleton (VERSIONING-07)."""

from methodology.versioning.pit_skeletons import (
    scenario_s03_playbook_release_with_description,
    scenario_s04_release_description_required,
)


def test_release_creates_major_version_with_description_skeleton():
    scenario_s03_playbook_release_with_description()


def test_release_without_description_blocked_skeleton():
    scenario_s04_release_description_required()
