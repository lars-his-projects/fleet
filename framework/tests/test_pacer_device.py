"""The pacer starts a worker run only while the worker is online (hub #24): `usage.fire` plans at most one run of the
lane `device` from the heartbeat of the worker, and `pacer.py` starts it with a dispatch of the worker workflow."""
import base64
import datetime
import json

import dashboard
import health
import pytest
import usage
from test_pacer_script import run

NOW = 1_800_000_000


def beat(minutes, worker="box"):
    """A heartbeat record that is `minutes` old at NOW."""
    at = datetime.datetime.fromtimestamp(NOW - minutes * 60, datetime.timezone.utc)
    return {"worker": worker, "time": f"{at:%Y-%m-%dT%H:%M:%SZ}", "kvm": False}


def ticket(number, lane="device"):
    return {"number": number, "title": f"Ticket {number}", "body": "", "created_at": "2020-01-01T00:00:00Z",
            "labels": [{"name": "P1"}, {"name": f"lane:{lane}"}]}


@pytest.fixture
def world(monkeypatch):
    """A false project for `usage.fire`: the open issues, the claim refs and the heartbeat files of `state`."""
    state = {"issues": [ticket(5)], "beats": [beat(10)], "refs": [], "calls": []}

    def api(path, method="GET", data=None, repo=None):
        state["calls"].append(path)
        if path == "contents/worker?ref=metrics":
            if state["beats"] is None:
                raise RuntimeError("HTTP 404")
            return [{"type": "file", "name": f"w{i}.json"} for i in range(len(state["beats"]))]
        if path.startswith("contents/worker/w"):
            text = json.dumps(state["beats"][int(path.split("worker/w")[1].split(".")[0])])
            return {"content": base64.b64encode(text.encode()).decode()}
        return {"total_count": 0}

    monkeypatch.setattr(dashboard, "RESERVED", ("haiku", "device"))
    monkeypatch.setattr(dashboard, "pages", lambda path, limit=10: state["issues"] if path.startswith("issues") else [])
    monkeypatch.setattr(dashboard, "api", api)
    monkeypatch.setattr(health, "claim_refs", lambda remote="origin": state["refs"])
    monkeypatch.setattr(health, "lane_weights", lambda comments: ({"haiku": 0.25}, {"haiku": "start"}))
    monkeypatch.setattr(usage, "due_reviews", lambda **_: [])
    monkeypatch.setattr(usage, "free_sources", lambda *a, **k: [])
    monkeypatch.setattr(usage, "release_due", lambda: [])
    return state


def fire(started=None):
    return usage.fire({"five_hour": (0.2, NOW + 3 * 3600, "allowed")}, NOW, status=([], ""), started=started, target=4)


def test_a_fresh_heartbeat_counts_as_online_and_an_old_or_bad_one_does_not():
    assert usage.worker_online([beat(59)], NOW, period=30)
    assert not usage.worker_online([beat(60)], NOW, period=30)
    assert usage.worker_online([beat(500), beat(5, "other")], NOW, period=30)
    assert not usage.worker_online([], NOW) and not usage.worker_online(None, NOW)
    assert not usage.worker_online([{"worker": "box"}, {"worker": "box", "time": "soon"}, {"time": None}], NOW)


def test_the_worker_online_and_a_ready_device_ticket_give_one_worker_run(world):
    world["issues"] = [ticket(5), ticket(6)]            # two tickets: still one run, the worker does one at a time
    k, runs, line = fire()
    assert (k, runs["device"], runs["haiku"]) == (1, 1, 0)
    assert "device 1 (ready 2)" in line and "ready 0 " in line   # no cloud run counts a device ticket as ready


def test_an_old_heartbeat_gives_no_worker_run(world):
    world["beats"] = [beat(61)]
    k, runs, _ = fire()
    assert (k, runs["device"]) == (0, 0)


def test_a_missing_heartbeat_gives_no_worker_run(world, capsys):
    world["beats"] = None                               # no folder `worker` on the branch metrics
    assert fire()[:2] == (0, {"haiku": 0, "device": 0})
    assert "no heartbeat of the worker" in capsys.readouterr().err
    world["beats"] = []
    assert fire()[0] == 0


def test_no_ready_device_ticket_gives_no_worker_run_and_no_heartbeat_read(world):
    world["issues"] = [ticket(7, "haiku")]
    k, runs, line = fire()
    assert (runs["device"], runs["haiku"]) == (0, 1) and "device" not in line.split("weights")[0]
    assert not any(c.startswith("contents/worker") for c in world["calls"])


def test_a_worker_run_that_works_or_starts_gives_no_second_run(world):
    world["refs"] = [f"5 {NOW - 60} Claim #5 by agent/5-x lane device"]
    world["issues"] = [ticket(6)]
    assert fire()[1]["device"] == 0                     # its claim beats
    world["refs"] = []
    assert fire(started={"device": 1})[1]["device"] == 0   # the last cycle started it: no claim yet
    assert fire()[1]["device"] == 1


def test_a_worker_run_needs_room_for_one_opus_run(world):
    world["refs"] = [f"{n} {NOW - 60} Claim #{n} by agent/{n}-x" for n in (1, 2, 3, 4)]   # the target is 4
    assert fire()[1]["device"] == 0
    world["refs"] = world["refs"][:3]
    assert fire()[:2] == (1, {"haiku": 0, "device": 1})


def test_a_paused_project_gets_no_worker_run():
    assert usage.device_runs(1, 0, 4, True, lambda: True) == 0
    assert usage.device_runs(1, 0, 4, False, lambda: True) == 1


@pytest.fixture
def github(monkeypatch):
    """A false GitHub for the dispatch: `state["runs"]` are the runs of the worker workflow; records each POST."""
    state = {"runs": [{"status": "completed"}], "posts": [], "fail": None}

    def api(path, method="GET", data=None, repo=None):
        if method == "POST":
            if state["fail"]:
                raise RuntimeError(state["fail"])
            state["posts"].append((path, data))
            raise json.JSONDecodeError("no body", "", 0)   # the answer 204
        return {"workflow_runs": state["runs"]}

    monkeypatch.setattr(dashboard, "api", api)
    return state


def test_a_planned_worker_run_gives_one_dispatch_also_with_a_starter_session(monkeypatch, github, capsys, tmp_path):
    log = tmp_path / "pacer.jsonl"
    assert run(monkeypatch, 2, {"haiku": 0, "device": 1}, {}, ["--log", str(log)], plan_only=True) == 0
    assert github["posts"] == [("actions/workflows/worker-run.yml/dispatches",
                                {"ref": "main", "inputs": {"prompt": "/scheduled max lane device"}})]
    record = json.loads(log.read_text().splitlines()[-1])
    assert (record["k"], record["plan"]) == (2, {"haiku": 0, "device": 1})   # the starter takes K less the lane runs
    assert record["started"] == {"haiku": 0, "main": 0, "device": 1} and record["problems"] == []
    assert "no URL" not in capsys.readouterr().out


def test_no_planned_worker_run_gives_no_dispatch(monkeypatch, github):
    assert run(monkeypatch, 1, {"haiku": 0, "device": 0}, {}, plan_only=True) == 0
    assert github["posts"] == []


def test_a_dry_run_sends_no_dispatch(monkeypatch, github, capsys):
    assert run(monkeypatch, 1, {"haiku": 0, "device": 1}, {}, ["--dry-run"], plan_only=True) == 0
    assert github["posts"] == [] and '"device": 1' in capsys.readouterr().out


def test_a_worker_run_that_waits_or_works_gives_no_dispatch(monkeypatch, github, capsys, tmp_path):
    github["runs"] = [{"status": "queued"}, {"status": "completed"}]
    log = tmp_path / "pacer.jsonl"
    assert run(monkeypatch, 1, {"haiku": 0, "device": 1}, {}, ["--log", str(log)], plan_only=True) == 0
    assert github["posts"] == []
    record = json.loads(log.read_text().splitlines()[-1])
    assert record["started"]["device"] == 0 and record["problems"] == ["no worker run: a worker run waits or works"]


def test_a_failed_dispatch_does_not_stop_the_cycle(monkeypatch, github, capsys):
    github["fail"] = "HTTP 404"
    assert run(monkeypatch, 1, {"haiku": 0, "device": 1}, {}, plan_only=True) == 0   # the plan of the cloud runs stays
    assert "no worker run: no dispatch of worker-run.yml (HTTP 404)" in capsys.readouterr().out
