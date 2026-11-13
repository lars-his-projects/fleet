"""The starts of the starter session of the fleet (roadmap `projects:auto`, decision A2 of card 6).

A project with `starts = "session"` in `[pacing]` has a pacer workflow that plans its runs each 10 minutes and writes
the plan to its branch `metrics`. That workflow sends no call. One starter session reads the newest plan of each
project and starts the runs in their repositories. So a project needs no scheduled task and no secret of its own.

`python3 -m hub.starts` prints one JSON line: `{"at", "starts": [...], "skipped": [...]}`. The starter session starts
one run for each item of `starts`, and nothing else.

The guards:
- The plan comes from the pacer workflow of the project (a script that reads the quota), not from a model.
- Only a project of `fleet.toml` with a weight above 0 whose newest record says `"starts": "session"` gets a start:
  the starter never starts a run in a project that starts its runs itself.
- A plan older than `STALE` starts nothing: a pacer loop that died starts no run.
- `LIMIT_PROJECT` and `LIMIT_TICK` are fixed limits for one tick, also for a wrong record.
- Only the lanes of `LANES` are known. The model of a lane is not in this repository: the starter session has it.
"""
import argparse
import datetime
import json
import sys
import tempfile

from fleetpage import sources
from hub import registry

UTC = datetime.timezone.utc
LANES = ("deep", "haiku", "main")   # the lanes that the starter knows, in the sequence of the starts
LIMIT_PROJECT = 4                   # the most starts for one project in one tick
LIMIT_TICK = 8                      # the most starts in one tick
STALE = 20 * 60                     # seconds: an older plan starts no run (the pacer writes one each 10 minutes)
SESSION = "session"                 # the value of `starts` in a record of a project that the starter serves


def prompt(lane):
    """The first message of a run: the same text as the scheduled task of the lane had."""
    return "/scheduled max" if lane == "main" else f"/scheduled max lane {lane}"


def start(project, lane, test=False):
    """One item of the list: all that the starter session needs to start one run, but the model."""
    return {"project": project.name, "lane": lane, "source_url": f"https://github.com/{project.repo}",
            "prompt": prompt(lane), "title": f"{project.name} run ({lane})" + (" selftest" if test else ""),
            "tags": ["fleet-run", f"project:{project.name}", f"lane:{lane}"] + ["fleet-selftest"] * test}


def seconds(record, now):
    """The age of a record in seconds, or None when its time does not parse."""
    try:
        at = datetime.datetime.strptime(record["at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except (KeyError, TypeError, ValueError):
        return None
    return now - at.timestamp()


def lanes_of(record):
    """The lanes of the runs that the plan of a record asks for, the lane runs first, or None for a wrong record."""
    k, plan = record.get("k"), record.get("plan") or {}
    if isinstance(k, bool) or not isinstance(k, int) or not isinstance(plan, dict):
        return None
    if any(isinstance(n, bool) or not isinstance(n, int) or n < 0 for n in plan.values()):
        return None
    out = [lane for lane in LANES if lane != "main" for _ in range(plan.get(lane, 0))]
    return out + ["main"] * max(0, k - sum(plan.values()))


def plan_starts(projects, records, now, limit_project=LIMIT_PROJECT, limit_tick=LIMIT_TICK, stale=STALE):
    """(starts, skipped) for one tick. projects: the `Project`s of the registry. records: {name: the newest pacer
    record or None}. now: Unix seconds. skipped: [{"project", "why"}] for each project with no start."""
    queues, skipped = [], []
    for p in projects:
        record = records.get(p.name)
        age = seconds(record, now) if record else None
        lanes = lanes_of(record) if record else None
        if p.weight <= 0:
            why = f"the stage {p.stage} has no quota"
        elif not record:
            why = "no pacer record"
        elif record.get("starts") != SESSION:
            why = "the project starts its runs itself"
        elif age is None or lanes is None:
            why = "the record is wrong"
        elif age > stale or age < -stale:
            why = f"the plan is {age / 60:.0f} minutes old"
        elif not lanes:
            why = "the plan asks for no run"
        else:
            queues.append([start(p, lane) for lane in lanes[:limit_project]])
            if len(lanes) > limit_project:
                skipped.append({"project": p.name, "why": f"{len(lanes) - limit_project} runs above the limit of a project"})
            continue
        skipped.append({"project": p.name, "why": why})
    starts = [q[i] for i in range(limit_project) for q in queues if i < len(q)]    # one of each project, then the next
    if len(starts) > limit_tick:
        skipped.append({"project": "*", "why": f"{len(starts) - limit_tick} runs above the limit of a tick"})
    return starts[:limit_tick], skipped


def newest(records):
    """The record with the newest time of a list of pacer records, or None."""
    timed = [r for r in records if isinstance(r, dict) and isinstance(r.get("at"), str)]
    return max(timed, key=lambda r: r["at"]) if timed else None


def read_newest(project):
    """The newest pacer record of a project from its branch `metrics` (a shallow clone), or None."""
    with tempfile.TemporaryDirectory() as folder:
        try:
            pacer, _ = sources.read_metrics(sources.clone_metrics(project.repo, f"{folder}/metrics"))
        except Exception:               # no branch, no network: this project gets no start, the others go on
            return None
    return newest(pacer)


def main(argv=None, read=read_newest, now=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default="fleet.toml")
    ap.add_argument("--selftest", action="store_true",
                    help="one Haiku-lane start for the first project that the starter serves, with no look at its plan")
    a = ap.parse_args(argv)
    try:
        fleet = registry.load(a.config)
    except registry.RegistryError as e:
        print(f"fleet.toml: {e}", file=sys.stderr)
        return 1
    now = datetime.datetime.now(UTC).timestamp() if now is None else now
    records = {p.name: read(p) for p in fleet.projects}
    if a.selftest:
        served = [p for p in fleet.projects if p.weight > 0 and (records.get(p.name) or {}).get("starts") == SESSION]
        starts, skipped = [start(p, "haiku", test=True) for p in served[:1]], []
    else:
        starts, skipped = plan_starts(fleet.projects, records, now)
    print(json.dumps({"at": f"{datetime.datetime.fromtimestamp(now, UTC):%Y-%m-%dT%H:%M:%SZ}", "starts": starts,
                      "skipped": skipped}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
