"""The lane `device` is no model: a plan with device runs gives no start of the starter session."""
from hub import starts
from tests.test_fleet_starts import NOW, fleet, record


def test_a_plan_with_device_runs_gives_no_start():
    got, skipped = starts.plan_starts(fleet(("alpha",)).projects, {"alpha": record(2, {"device": 2})}, NOW)
    assert got == [] and len(skipped) == 1


def test_device_runs_never_become_starts_beside_other_lanes():
    got, _ = starts.plan_starts(fleet(("alpha",)).projects, {"alpha": record(3, {"device": 1, "sonnet": 1})}, NOW)
    assert [s["lane"] for s in got] == ["sonnet", "opus"]
