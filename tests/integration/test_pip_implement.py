"""S06 PIP aggregated minor skeleton."""

from methodology.versioning.pit_skeletons import scenario_s06_pip_single_aggregate_minor


def test_pip_with_n_changes_produces_single_minor_bump_skeleton():
    scenario_s06_pip_single_aggregate_minor()
