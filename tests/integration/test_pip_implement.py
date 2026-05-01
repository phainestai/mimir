"""S06 PIP aggregated minor skeleton."""

from methodology.versioning.pit_skeletons import (
    scenario_s06_pip_single_aggregate_minor,
    scenario_s07_pip_sequential_minors,
)


def test_pip_with_n_changes_produces_single_minor_bump_skeleton():
    scenario_s06_pip_single_aggregate_minor()


def test_sequential_pips_increment_minor_skeleton():
    scenario_s07_pip_sequential_minors()
