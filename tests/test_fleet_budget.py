"""The one budget of the fleet in advice mode (`hub/budget.py`)."""
from hub import budget

NOW = 1_794_600_000     # an epoch second; a cycle is 600 s


def project(name, weight, work=True, spent=0.0):
    return {"name": name, "weight": weight, "work": work, "spent": spent}


def test_behind_the_pace_there_is_no_limit():
    out = budget.allocate(used=0.10, hours_left=84, burn=0.005, projects=[project("a", 2), project("b", 1, work=False)], now=NOW)
    assert out["mode"] == "free" and out["pace"] == 0.5
    assert out["projects"]["a"]["runs"] is None and out["projects"]["b"]["runs"] == 0


def test_ahead_of_the_pace_the_rate_is_the_rest_of_the_budget():
    out = budget.allocate(used=0.60, hours_left=84, burn=0.005, projects=[project("a", 1)], now=NOW)
    assert out["mode"] == "paced" and out["rate"] == round(0.40 / 84 / 0.005, 3)
    assert out["projects"]["a"]["runs"] == out["slots"]


def test_the_reserve_lowers_the_cap_and_is_free_again_at_the_end_of_the_week():
    assert budget.cap(0.10, hours_left=100) == 0.9 and budget.cap(0.10, hours_left=12) == 1.0
    early = budget.allocate(used=0.60, hours_left=84, burn=0.005, projects=[project("a", 1)], now=NOW, reserve=0.10)
    assert early["cap"] == 0.9 and early["pace"] == 0.45 and early["rate"] == round(0.30 / 84 / 0.005, 3)
    full = budget.allocate(used=0.95, hours_left=40, burn=0.005, projects=[project("a", 1)], now=NOW, reserve=0.10)
    assert full["rate"] == 0.0 and full["projects"]["a"]["runs"] == 0       # only the reserve is left: no run
    late = budget.allocate(used=0.95, hours_left=10, burn=0.005, projects=[project("a", 1)], now=NOW, reserve=0.10)
    assert late["cap"] == 1.0 and late["rate"] == 1.0


def test_a_part_of_a_run_becomes_a_turn_and_the_mean_is_the_rate():
    counts = [budget.slots(0.4, NOW + i * budget.CYCLE) for i in range(1000)]
    assert set(counts) == {0, 1} and abs(sum(counts) / 1000 - 0.4) < 0.02
    counts = [budget.slots(2.25, NOW + i * budget.CYCLE) for i in range(1000)]
    assert set(counts) == {2, 3} and abs(sum(counts) / 1000 - 2.25) < 0.02
    assert budget.slots(0, NOW) == 0 and budget.slots(-1, NOW) == 0


def test_the_slot_goes_to_the_project_that_is_most_below_its_share():
    projects = [project("a", 2, spent=90.0), project("b", 2, spent=10.0), project("c", 1, work=False, spent=50.0)]
    out = budget.allocate(used=0.60, hours_left=80, burn=0.005, projects=projects, now=NOW)
    rows = out["projects"]
    assert (rows["a"]["share"], rows["b"]["share"], rows["c"]["share"]) == (0.5, 0.5, 0.0)
    assert (rows["a"]["actual"], rows["b"]["actual"]) == (0.9, 0.1)
    assert out["slots"] >= 1 and rows["b"]["runs"] >= 1 and rows["b"]["runs"] >= rows["a"]["runs"] and rows["c"]["runs"] == 0


def test_more_slots_are_spread_by_weight():
    projects = [project("a", 3), project("b", 1)]
    out = budget.allocate(used=0.50, hours_left=100, burn=0.001, projects=projects, now=NOW)    # rate 5.0
    assert out["slots"] == 5 and out["projects"]["a"]["runs"] + out["projects"]["b"]["runs"] == 5
    assert out["projects"]["a"]["runs"] > out["projects"]["b"]["runs"] >= 1


def test_no_project_with_work_gets_no_slot():
    out = budget.allocate(used=0.60, hours_left=84, burn=0.005, projects=[project("a", 1, work=False)], now=NOW)
    assert out["slots"] == 0 and out["projects"]["a"]["runs"] == 0
