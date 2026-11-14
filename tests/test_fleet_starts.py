"""The list of starts for the starter session (`hub/starts.py`): the plan of each pacer workflow, with fixed limits."""
import json

from hub import registry, starts

NOW = 1_794_600_000
CONFIG = """
[fleet]
owner = "o"
org = "g"
[stages]
build = 3
paused = 0
[projects.alpha]
repo = "g/alpha"
stage = "build"
[projects.beta]
repo = "g/beta"
stage = "build"
[projects.gamma]
repo = "g/gamma"
stage = "paused"
"""


def fleet(names=("alpha", "beta"), stage="build"):
    return registry.parse({"fleet": {"owner": "o", "org": "g"}, "stages": {"build": 3, "paused": 0},
                           "projects": {n: {"repo": f"g/{n}", "stage": stage} for n in names}})


def at(seconds_ago=60):
    import datetime
    return f"{datetime.datetime.fromtimestamp(NOW - seconds_ago, datetime.timezone.utc):%Y-%m-%dT%H:%M:%SZ}"


def record(k, plan=None, ago=60, **more):
    return {"at": at(ago), "k": k, "plan": plan or {}, "starts": "session", **more}


def test_a_plan_becomes_starts_with_the_lane_runs_first():
    got, skipped = starts.plan_starts(fleet(("alpha",)).projects, {"alpha": record(5, {"haiku": 1, "sonnet": 1, "fable": 1})}, NOW)
    assert [s["lane"] for s in got] == ["fable", "sonnet", "haiku", "opus"] and len(skipped) == 1
    assert got[0] == {"project": "alpha", "lane": "fable", "source_url": "https://github.com/g/alpha",
                      "prompt": "/scheduled max lane fable", "title": "alpha run (fable)",
                      "tags": ["fleet-run", "project:alpha", "lane:fable"]}
    assert got[3]["prompt"] == "/scheduled max"


def test_only_a_fresh_plan_of_a_project_that_the_starter_serves_starts_a_run():
    projects = fleet(("alpha", "beta")).projects
    cases = {
        "no pacer record": None,
        "the project starts its runs itself": {"at": at(), "k": 2, "plan": {}},
        "the plan is 30 minutes old": record(2, ago=30 * 60),
        "the plan asks for no run": record(0, {"haiku": 0}),
        "the record is wrong": record("2"),
    }
    for why, rec in cases.items():
        got, skipped = starts.plan_starts(projects, {"alpha": rec, "beta": record(1)}, NOW)
        assert [s["project"] for s in got] == ["beta"], why
        assert {"project": "alpha", "why": why} in skipped, why
    for wrong in (record(2, {"haiku": -1}), record(True), record(2, ["haiku"]), {"k": 1, "plan": {}, "starts": "session"},
                  record(1, ago=-3600)):
        assert starts.plan_starts(projects, {"alpha": wrong}, NOW)[0] == []


def test_a_stage_with_no_quota_gets_no_start():
    got, skipped = starts.plan_starts(fleet(("alpha",), stage="paused").projects, {"alpha": record(2)}, NOW)
    assert got == [] and skipped == [{"project": "alpha", "why": "the stage paused has no quota"}]


def test_the_limits_hold_for_a_wrong_plan_and_each_project_gets_a_turn():
    projects = fleet(("alpha", "beta", "gamma")).projects
    got, skipped = starts.plan_starts(projects[:1], {"alpha": record(10)}, NOW)
    assert len(got) == starts.LIMIT_PROJECT
    assert {"project": "alpha", "why": "6 runs above the limit of a project"} in skipped
    got, skipped = starts.plan_starts(projects, {n: record(4) for n in ("alpha", "beta", "gamma")}, NOW)
    assert len(got) == starts.LIMIT_TICK and [s["project"] for s in got[:3]] == ["alpha", "beta", "gamma"]
    assert {"project": "*", "why": "4 runs above the limit of a tick"} in skipped
    assert starts.plan_starts(projects[:1], {"alpha": record(3, {"night": 2})}, NOW)[0][0]["lane"] == "opus"   # an unknown lane gets no start


def test_newest_takes_the_record_with_the_newest_time():
    assert starts.newest([{"at": "2026-11-13T10:00:00Z", "k": 1}, "x", {"k": 5}, {"at": "2026-11-13T12:00:00Z", "k": 2}])["k"] == 2
    assert starts.newest([]) is None and starts.newest([{"k": 1}]) is None


def test_the_command_prints_one_json_line(tmp_path, capsys):
    (tmp_path / "fleet.toml").write_text(CONFIG)
    records = {"alpha": {"at": at(), "k": 1, "plan": {}}, "beta": record(2, {"haiku": 1}), "gamma": record(1)}
    code = starts.main(["--config", str(tmp_path / "fleet.toml")], read=lambda p: records[p.name], now=NOW)
    out = json.loads(capsys.readouterr().out)
    assert code == 0 and [(s["project"], s["lane"]) for s in out["starts"]] == [("beta", "haiku"), ("beta", "opus")]
    assert {s["project"] for s in out["skipped"]} == {"alpha", "gamma"} and out["at"] == at(0)


def test_the_selftest_gives_one_haiku_start_for_the_first_served_project(tmp_path, capsys):
    (tmp_path / "fleet.toml").write_text(CONFIG)
    records = {"alpha": {"at": at(), "k": 0, "plan": {}}, "beta": record(0), "gamma": record(0)}
    assert starts.main(["--config", str(tmp_path / "fleet.toml"), "--selftest"], read=lambda p: records[p.name], now=NOW) == 0
    out = json.loads(capsys.readouterr().out)
    assert [(s["project"], s["lane"], s["prompt"]) for s in out["starts"]] == [("beta", "haiku", "/scheduled max lane haiku")]
    assert "fleet-selftest" in out["starts"][0]["tags"] and out["starts"][0]["title"].endswith("selftest")


def test_a_fault_in_the_registry_gives_exit_1_and_no_start(tmp_path, capsys):
    (tmp_path / "fleet.toml").write_text(CONFIG.replace('stage = "paused"', 'stage = "later"'))
    assert starts.main(["--config", str(tmp_path / "fleet.toml")], read=lambda p: None, now=NOW) == 1
    assert capsys.readouterr().out == ""
