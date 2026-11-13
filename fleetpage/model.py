"""The numbers of the fleet page: pure functions over the loaded data (no network, no clock of their own).

The data of a project comes from its `metrics` branch (the pacer records and the run reports), its roadmap file and
its open `needs-human` issues. `build()` joins them into one dict, the model, that `page.render()` shows and that the
build also writes as `data.json`.

All projects use one Claude account, so each pacer record shows the same quota. A second account needs a change here.
"""
import datetime
import re

from hub import budget

UTC = datetime.timezone.utc
WEEK = 7 * 24 * 3600        # seconds of one quota week
BUCKET = 2                  # hours of one point of the weekly curve
LIMIT = 0.98                # the 7-day usage from which the runs stop
KINDS = ("decision", "check", "epic", "bug", "question")   # the order of the inbox

GOAL = re.compile(r"^## +\d+\. +(.*)$")
FEATURE = re.compile(r"^- \[([ xX])\] (?:\(#\d+\) )?`[a-z0-9-]+:[a-z0-9-]+`")   # the epic number can come before the key
WALL = re.compile(r"wall (\d+(?:\.\d+)?) min")
PAUSED = re.compile(r"paused (True|False)")


def ts(text):
    """An aware datetime from `2026-11-13T17:32:06Z`."""
    return datetime.datetime.strptime(text[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)


def iso(value):
    """`2026-11-13T17:32:06Z` from a datetime or from epoch seconds."""
    if not isinstance(value, datetime.datetime):
        value = datetime.datetime.fromtimestamp(value, UTC)
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_roadmap(text):
    """[{title, done, total}] for each goal `## N. Title` and its feature lines ``- [x] `goal:key` ...``.

    A heading with no number (for example `## Principles`) ends the goals. The code names after a title
    (`` (`game/`) ``) are not part of the title.
    """
    goals, current = [], None
    for line in (text or "").splitlines():
        m = GOAL.match(line)
        if m:
            current = {"title": m.group(1).split(" (`")[0].strip(), "done": 0, "total": 0}
            goals.append(current)
        elif line.startswith("## "):
            current = None
        elif current is not None:
            f = FEATURE.match(line)
            if f:
                current["total"] += 1
                current["done"] += f.group(1) != " "
    return goals


def usage_weeks(records, keep=3):
    """The 7-day usage curve of the newest `keep` quota weeks, from the pacer records of all projects.

    A week is the 7 days before a reset time of the 7-day window. `points` are [hours after the start, usage 0..1],
    one per `BUCKET` hours; the usage only grows in a week. `limit_hour` is the first hour at `LIMIT` or more.
    """
    by_reset = {}
    for r in records:
        window, at = r.get("seven_day"), r.get("at")
        if not at or not window or len(window) < 2 or not window[1]:
            continue
        by_reset.setdefault(int(window[1]), []).append((ts(at).timestamp(), float(window[0] or 0)))
    weeks = []
    for reset in sorted(by_reset)[-keep:]:
        start, buckets, limit = reset - WEEK, {}, None
        for at, used in sorted(by_reset[reset]):
            hour = (at - start) / 3600
            if not 0 <= hour <= 168:
                continue        # a record whose reset time does not fit its own time
            b = int(hour // BUCKET) * BUCKET
            buckets[b] = max(buckets.get(b, 0.0), used)
            if limit is None and used >= LIMIT:
                limit = hour
        points, top = [[0.0, 0.0]], 0.0
        for b in sorted(buckets):
            top = max(top, buckets[b])
            points.append([min(b + BUCKET / 2, 168.0), round(top, 4)])
        weeks.append({"start": iso(start), "end": iso(reset), "points": points, "max": round(top, 4),
                      "limit_hour": None if limit is None else round(limit, 1)})
    return weeks


def week_of(when, weeks):
    """The index in `weeks` of the quota week that holds the datetime `when`, or None."""
    for i, w in enumerate(weeks):
        if ts(w["start"]) <= when < ts(w["end"]):
            return i
    return None


def report_stats(report):
    """(merged PRs, usage in USD at API prices, lane, wall minutes of the session, session) of one run report."""
    tickets = report.get("tickets") or []
    prs = sum(1 for t in tickets if str(t.get("result", "")).startswith("pr #"))
    usd = float((report.get("tokens") or {}).get("usd") or 0)
    lane = report.get("lane") or "main"
    wall = WALL.search(report.get("body") or "")
    return prs, usd, "main" if lane == "opus" else lane, float(wall.group(1)) if wall else 0.0, report.get("session") or ""


def project_runs(reports, weeks, now):
    """The run numbers of one project: for each quota week, for each lane, and for the last 24 hours and 7 days.

    A run can post several reports. Its run-hours are the largest `wall` value of its session, in the week of that report.
    """
    per_week = [{"reports": 0, "prs": 0, "usd": 0.0, "hours": 0.0} for _ in weeks]
    lanes, sessions, last, first = {}, {}, None, None
    reports_24h = prs_7d = 0
    usd_7d = 0.0
    for n, r in enumerate(reports):
        if not r.get("created_at"):
            continue
        when = ts(r["created_at"])
        prs, usd, lane, wall, session = report_stats(r)
        last = when if last is None or when > last else last
        first = when if first is None or when < first else first
        age = (now - when).total_seconds()
        reports_24h += 0 <= age <= 86400
        if 0 <= age <= WEEK:
            prs_7d += prs
            usd_7d += usd
        e = lanes.setdefault(lane, {"reports": 0, "prs": 0, "usd": 0.0, "nopr_usd": 0.0})
        e["reports"] += 1
        e["prs"] += prs
        e["usd"] += usd
        e["nopr_usd"] += usd if prs == 0 else 0.0
        w = week_of(when, weeks)
        if w is not None:
            per_week[w]["reports"] += 1
            per_week[w]["prs"] += prs
            per_week[w]["usd"] += usd
            key = session or f"report-{n}"
            if key not in sessions or wall > sessions[key][1]:
                sessions[key] = (w, wall)
    for w, wall in sessions.values():
        per_week[w]["hours"] += wall / 60
    return {"weeks": per_week, "lanes": lanes, "first_report": iso(first) if first else None,
            "last_report": iso(last) if last else None, "reports_24h": reports_24h, "prs_7d": prs_7d, "usd_7d": usd_7d}


def pacer_state(records, weeks, now):
    """The newest pacer record of one project, and the share of its cycles with no work in the newest quota week."""
    dated = [r for r in records if r.get("at")]
    if not dated:
        return None
    newest = max(dated, key=lambda r: r["at"])
    paused = PAUSED.search(newest.get("line") or "")
    cycles = idle = 0
    for r in dated:
        if weeks and week_of(ts(r["at"]), weeks) == len(weeks) - 1:
            cycles += 1
            idle += not r.get("ready") and not r.get("claims")
    return {"at": newest["at"], "age_minutes": round((now - ts(newest["at"])).total_seconds() / 60),
            "target": newest.get("target"), "claims": newest.get("claims") or 0, "ready": newest.get("ready") or 0,
            "paused": bool(paused and paused.group(1) == "True"), "problems": list(newest.get("problems") or []),
            "refill": newest.get("refill") or 0, "burn7": newest.get("burn7"),
            "idle_week": round(idle / cycles, 3) if cycles else None}


def quota_now(records, now):
    """The 5-hour and the 7-day window from the newest pacer record of all projects, or None."""
    dated = [r for r in records if r.get("at") and r.get("seven_day") and r.get("five_hour")]
    if not dated:
        return None
    r = max(dated, key=lambda r: r["at"])
    reset = int(r["seven_day"][1])
    hours = (now.timestamp() - (reset - WEEK)) / 3600
    return {"at": r["at"], "age_minutes": round((now - ts(r["at"])).total_seconds() / 60),
            "five_hour": {"used": float(r["five_hour"][0] or 0), "resets": iso(int(r["five_hour"][1]))},
            "seven_day": {"used": float(r["seven_day"][0] or 0), "resets": iso(reset)},
            "week_hours": round(max(0.0, min(168.0, hours)), 1), "pace": round(max(0.0, min(1.0, hours / 168)), 4)}


def classify(issue):
    """(kind, the persons that the ticket names) of a `needs-human` issue. The kinds are `KINDS`. The persons are the
    assignees of the issue (owner, 2026-11-13). A card with no assignee can still have the old label `for-<name>`."""
    title = (issue.get("title") or "").lower()
    labels = [label if isinstance(label, str) else label.get("name", "") for label in issue.get("labels") or []]
    if "decision" in labels or title.startswith("decide"):
        kind = "decision"
    elif title.startswith("check"):
        kind = "check"
    elif "epic" in labels:
        kind = "epic"
    elif "bug" in labels:
        kind = "bug"
    else:
        kind = "question"
    who = [a if isinstance(a, str) else a.get("login", "") for a in issue.get("assignees") or []]
    return kind, sorted(w for w in who if w) or sorted(label[4:] for label in labels if label.startswith("for-"))


def waiting(issues, repo, now):
    """The inbox rows of one project: its open `needs-human` issues, sorted by kind and then the newest first."""
    rows = []
    for issue in issues:
        kind, who = classify(issue)
        created = issue.get("created_at")
        rows.append({"number": issue.get("number"), "title": issue.get("title") or "", "kind": kind, "for": who,
                     "url": issue.get("html_url") or f"https://github.com/{repo}/issues/{issue.get('number')}",
                     "days": round((now - ts(created)).total_seconds() / 86400, 1) if created else None})
    return sorted(rows, key=lambda r: (KINDS.index(r["kind"]), -(r["number"] or 0)))


def fleet_budget(fleet, quota, projects, weeks, now):
    """The advice of the one budget for this cycle (`hub/budget.py`), or None with no quota record.

    A project has work when its pacer sees a ready ticket, a run at work or a refill. The burn of one run-hour is the
    median of the values that the pacers of the projects measured.
    """
    if not quota:
        return None
    burns = sorted(p["pacer"]["burn7"] for p in projects if p["pacer"] and p["pacer"].get("burn7"))
    burn = burns[len(burns) // 2] if burns else 0.005
    current = weeks[-1]["split"] if weeks and weeks[-1]["current"] else {}
    rows = [{"name": p["name"], "weight": p["weight"], "spent": current.get(p["name"], {}).get("usd", 0.0),
             "work": bool(p["pacer"] and (p["pacer"]["ready"] or p["pacer"]["claims"] or p["pacer"]["refill"]))}
            for p in projects]
    advice = budget.allocate(quota["seven_day"]["used"], 168 - quota["week_hours"], burn, rows, now.timestamp(),
                             reserve=fleet.week_reserve)
    advice["burn"] = burn
    return advice


def build(fleet, loaded, now):
    """The model of the page.

    `loaded`: {project name: {"pacer": [records], "reports": [run reports], "roadmap": text or None,
    "waiting": [issues] or None, "errors": [text]}}. None means that the read failed: the page says so.
    """
    all_pacer = [r for d in loaded.values() for r in d.get("pacer") or []]
    weeks = usage_weeks(all_pacer)
    total_weight = sum(p.weight for p in fleet.projects) or 1.0
    projects, lanes, firsts = [], {}, []
    for w in weeks:
        w["split"], w["usd"], w["hours"] = {}, 0.0, 0.0
        w["current"] = ts(w["start"]) <= now < ts(w["end"])
    for p in fleet.projects:
        d = loaded.get(p.name) or {}
        runs = project_runs(d.get("reports") or [], weeks, now)
        for w, numbers in zip(weeks, runs["weeks"]):
            if numbers["reports"]:
                w["split"][p.name] = {k: round(v, 2) for k, v in numbers.items()}
                w["usd"] = round(w["usd"] + numbers["usd"], 2)
                w["hours"] = round(w["hours"] + numbers["hours"], 2)
        for lane, numbers in runs["lanes"].items():
            e = lanes.setdefault(lane, {"reports": 0, "prs": 0, "usd": 0.0, "nopr_usd": 0.0})
            for k, v in numbers.items():
                e[k] += v
        if runs["first_report"]:
            firsts.append(runs["first_report"])
        goals = parse_roadmap(d.get("roadmap")) if d.get("roadmap") is not None else None
        issues = d.get("waiting")
        projects.append({
            "name": p.name, "repo": p.repo, "what": p.what, "stage": p.stage, "weight": p.weight,
            "share": round(p.weight / total_weight, 4), "owners": list(p.owners), "links": dict(p.links),
            "goals": goals, "done": sum(g["done"] for g in goals or []), "total": sum(g["total"] for g in goals or []),
            "waiting": None if issues is None else waiting(issues, p.repo, now),
            "pacer": pacer_state(d.get("pacer") or [], weeks, now),
            "last_report": runs["last_report"], "reports_24h": runs["reports_24h"], "prs_7d": runs["prs_7d"],
            "usd_7d": round(runs["usd_7d"], 2), "errors": list(d.get("errors") or [])})
    order = {"haiku": 0, "main": 1, "deep": 2}
    quota = quota_now(all_pacer, now)
    return {
        "generated": iso(now),
        "fleet": {"owner": fleet.owner, "org": fleet.org, "agent": fleet.agent, "week_reserve": fleet.week_reserve,
                  "attention_minutes": fleet.attention_minutes},
        "quota": quota,
        "budget": fleet_budget(fleet, quota, projects, weeks, now),
        "weeks": weeks,
        "lanes": [{"lane": lane, **{k: round(v, 2) for k, v in lanes[lane].items()}}
                  for lane in sorted(lanes, key=lambda x: (order.get(x, 9), x))],
        "lanes_since": min(firsts) if firsts else None,
        "projects": projects,
        "totals": {"done": sum(p["done"] for p in projects), "total": sum(p["total"] for p in projects),
                   "waiting": sum(len(p["waiting"] or []) for p in projects),
                   "ready": sum((p["pacer"] or {}).get("ready", 0) for p in projects),
                   "claims": sum((p["pacer"] or {}).get("claims", 0) for p in projects),
                   "prs_7d": sum(p["prs_7d"] for p in projects), "usd_7d": round(sum(p["usd_7d"] for p in projects), 2)},
    }
