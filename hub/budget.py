"""The one budget of the fleet: how many runs each project can have now (roadmap `pacer:one`).

All projects share the quota of one subscription. This module gives the split in "advice" mode: the fleet page shows
it, and no pacer follows it yet. It is a pure function, so that it can be tested and watched before it controls a run.

The rule:
- The runs can use the week up to `cap`: 1 minus the reserve for the owner. The reserve is free again in the last
  `RELEASE` hours of the week, so that the week ends near 100 %.
- An even pace: at each moment the usage should be `cap` times the part of the week that passed.
- Behind the pace: no limit (mode `free`). Each project follows its own pacer.
- Ahead of the pace (mode `paced`): the rest of the budget carries `rate` runs to the reset. `rate` is small, about
  1 run for the whole account, so a part of a run becomes a turn: `slots()` gives one more run in a part of the
  10-minute cycles.
- The slots go to the projects that have work. The project that is most below its share of the week (its weight)
  gets the next slot.
"""
import math

RELEASE = 12            # hours before the weekly reset from which the runs can use the reserve
CYCLE = 600             # seconds of one pacer cycle
GOLDEN = 0.6180339887   # the step of the phase: the turns of a part of a run are spread evenly over the cycles


def cap(reserve, hours_left, release=RELEASE):
    """The share of the week that the runs can use now."""
    return 1.0 if hours_left <= release else 1.0 - reserve


def slots(rate, now):
    """The whole number of runs for this cycle: over many cycles the mean is `rate`."""
    if rate <= 0:
        return 0
    phase = (int(now // CYCLE) * GOLDEN) % 1.0
    return math.floor(rate) + (1 if rate - math.floor(rate) > phase else 0)


def allocate(used, hours_left, burn, projects, now, reserve=0.0, release=RELEASE):
    """The advice of the budget for this cycle.

    `used`: the 7-day usage (0..1). `hours_left`: hours to the weekly reset. `burn`: the share of the week that one
    run uses in one hour. `projects`: [{"name", "weight", "work": bool, "spent": the usage of this week in any unit}].
    `now`: epoch seconds. Returns {"mode", "cap", "pace", "rate", "slots", "projects": {name: {"share", "actual",
    "runs"}}}. `runs` is None in the mode `free` (no limit), and 0 for a project with no work.
    """
    hours_left = max(hours_left, 0.25)
    limit = cap(reserve, hours_left, release)
    pace = limit * max(0.0, min(1.0, 1 - hours_left / 168))
    active = [p for p in projects if p.get("work") and p.get("weight", 0) > 0]
    weight = sum(p["weight"] for p in active) or 1.0
    spent = sum(p.get("spent", 0.0) for p in active)
    rows = {p["name"]: {"share": round(p["weight"] / weight, 4) if p in active else 0.0,
                        "actual": round(p.get("spent", 0.0) / spent, 4) if p in active and spent else 0.0,
                        "runs": 0} for p in projects}
    out = {"mode": "paced", "cap": limit, "pace": round(pace, 4), "rate": None, "slots": None, "projects": rows}
    if used <= pace:
        out["mode"] = "free"
        for p in active:
            rows[p["name"]]["runs"] = None
        return out
    rate = max(limit - used, 0.0) / hours_left / burn if burn > 0 else 0.0
    n = slots(rate, now) if active else 0
    out["rate"], out["slots"] = round(rate, 3), n
    given = {p["name"]: 0 for p in active}
    for _ in range(n):      # the next slot: the project that is most below its share, with the slots of this cycle
        name = max(given, key=lambda k: (rows[k]["share"] - rows[k]["actual"] - given[k] / max(n, 1), rows[k]["share"]))
        given[name] += 1
    for name, k in given.items():
        rows[name]["runs"] = k
    return out
