"""S12–S15 History UI skeleton tests."""

from methodology.versioning.pit_skeletons import (
    scenario_s12_history_timeline_ui,
    scenario_s13_historical_version_view,
    scenario_s14_version_compare_split_pane,
    scenario_s15_pip_rows_in_history,
)


def test_major_minor_visual_distinction_skeleton():
    scenario_s12_history_timeline_ui()


def test_view_historical_version_skeleton():
    scenario_s13_historical_version_view()


def test_compare_versions_split_pane_skeleton():
    scenario_s14_version_compare_split_pane()


def test_pip_sourced_rows_link_to_pip_skeleton():
    scenario_s15_pip_rows_in_history()
