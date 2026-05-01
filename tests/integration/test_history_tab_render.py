"""S12–S15 History UI skeleton tests."""

from methodology.versioning.pit_skeletons import (
    scenario_s12_history_timeline_ui,
    scenario_s13_historical_version_view,
)


def test_major_minor_visual_distinction_skeleton():
    scenario_s12_history_timeline_ui()


def test_view_historical_version_skeleton():
    scenario_s13_historical_version_view()
