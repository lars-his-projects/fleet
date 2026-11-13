"""The numbers of the fleet page (`dashboard/model.py`), with small made-up data."""
from dashboard import model
from hub import registry

NOW = model.ts("2026-11-13T18:00:00Z")
RESET = int(model.ts("2026-11-20T04:00:00Z").timestamp())      # the quota week of NOW starts on 13 Nov, 04:00 UTC
BEFORE = RESET - model.WEEK                                    # the reset of the week before


def pacer(at, used, reset=RESET, ready=0, claims=0, paused=False):
    return {"at": at, "seven_day": [used, reset, "allowed"], "five_hour": [0.2, reset - 3600, "allowed"], "target": 4,
            "ready": ready, "claims": claims, "problems": [], "line": f"five_hour 20% · paused {paused} · flow ok"}


def report(at, lane="opus", prs=1, usd=1.0, wall=10, session="s1"):
    return {"created_at": at, "lane": lane, "session": session, "tokens": {"usd": usd},
            "tickets": [{"result": "pr #5"}] * prs + [{"result": "no change"}],
            "body": f"Text.\n\nRun: {session} · branch b · wall {wall} min · model m"}


FLEET = registry.parse({
    "fleet": {"owner": "o", "org": "g", "week_reserve": 0.1, "attention_minutes": 30},
    "stages": {"build": 3, "polish": 1},
    "projects": {"alpha": {"repo": "g/alpha", "stage": "build"}, "beta": {"repo": "g/beta", "stage": "polish"}},
})


def test_roadmap_counts_the_feature_lines_of_each_numbered_goal():
    text = ("# Roadmap\n- [x] `x:before` no goal yet\n## 1. Convert maps (`a.py`, `b.py`)\n- [x] `convert:one` a (#1)\n"
            "  - a sub-item\n- [ ] `convert:two` b\n## 2. Play\n- [X] `play:one` c\n- [x] (#12) `play:two` the epic number first\n"
            "- [x] a line with no key\n## Principles\n- [x] `p:one` not a feature\n")
    assert model.parse_roadmap(text) == [{"title": "Convert maps", "done": 1, "total": 2}, {"title": "Play", "done": 2, "total": 2}]
    assert model.parse_roadmap("") == []


def test_usage_weeks_group_by_the_reset_and_find_the_limit():
    records = [pacer("2026-11-06T05:00:00Z", 0.10, BEFORE), pacer("2026-11-12T09:30:00Z", 0.98, BEFORE),
               pacer("2026-11-12T20:00:00Z", 1.00, BEFORE), pacer("2026-11-13T05:00:00Z", 0.02), pacer("2026-11-13T17:00:00Z", 0.07),
               {"at": "2026-11-13T17:10:00Z"}]
    before, current = model.usage_weeks(records)
    assert (before["start"], before["end"]) == ("2026-11-06T04:00:00Z", "2026-11-13T04:00:00Z")
    assert before["max"] == 1.0 and before["limit_hour"] == 149.5
    assert current["limit_hour"] is None and current["points"][0] == [0.0, 0.0] and current["points"][-1] == [13.0, 0.07]
    assert all(a[1] <= b[1] for a, b in zip(before["points"], before["points"][1:]))
    assert len(model.usage_weeks(records, keep=1)) == 1


def test_project_runs_count_prs_usage_lanes_and_the_hours_of_a_session_one_time():
    weeks = model.usage_weeks([pacer("2026-11-13T05:00:00Z", 0.02)])
    reports = [report("2026-11-13T10:00:00Z", wall=5), report("2026-11-13T10:20:00Z", wall=12),
               report("2026-11-13T11:00:00Z", lane="haiku", prs=0, usd=0.5, wall=6, session="s2"),
               report("2026-11-01T11:00:00Z", lane="deep", prs=2, usd=4.0, wall=30, session="s3")]
    runs = model.project_runs(reports, weeks, NOW)
    week = runs["weeks"][0]
    assert (week["reports"], week["prs"], week["usd"]) == (3, 2, 2.5)
    assert round(week["hours"], 6) == 0.3       # s1: its largest wall value (12 minutes); s2: 6 minutes
    assert runs["lanes"]["main"] == {"reports": 2, "prs": 2, "usd": 2.0, "nopr_usd": 0.0}
    assert runs["lanes"]["haiku"]["nopr_usd"] == 0.5 and runs["lanes"]["deep"]["prs"] == 2
    assert (runs["reports_24h"], runs["prs_7d"], runs["last_report"]) == (3, 2, "2026-11-13T11:00:00Z")


def test_pacer_state_takes_the_newest_record_and_the_share_of_cycles_with_no_work():
    records = [pacer("2026-11-13T05:00:00Z", 0.02, ready=2, claims=1), pacer("2026-11-13T06:00:00Z", 0.03),
               pacer("2026-11-13T17:30:00Z", 0.07, paused=True), pacer("2026-11-12T06:00:00Z", 0.9, BEFORE)]
    state = model.pacer_state(records, model.usage_weeks(records), NOW)
    assert (state["at"], state["age_minutes"], state["paused"], state["idle_week"]) == ("2026-11-13T17:30:00Z", 30, True, 0.667)
    assert model.pacer_state([], [], NOW) is None


def test_quota_now_gives_the_pace_of_the_week():
    quota = model.quota_now([pacer("2026-11-13T17:30:00Z", 0.07)], NOW)
    assert quota["seven_day"] == {"used": 0.07, "resets": "2026-11-20T04:00:00Z"}
    assert quota["week_hours"] == 14.0 and quota["pace"] == round(14 / 168, 4)
    assert model.quota_now([], NOW) is None


def test_classify_reads_the_kind_and_the_persons():
    assert model.classify({"title": "Decide: which settings stay", "labels": ["for-lars", "P2"]}) == ("decision", ["lars"])
    assert model.classify({"title": "Check: the message on a phone", "labels": [{"name": "for-jeroen"}]}) == ("check", ["jeroen"])
    assert model.classify({"title": "Put the site live", "labels": ["epic", "bug"]}) == ("epic", [])
    assert model.classify({"title": "Fix it", "labels": ["bug"]}) == ("bug", [])
    assert model.classify({"title": None, "labels": None}) == ("question", [])


def test_build_joins_the_projects_and_keeps_a_failed_read_visible():
    loaded = {
        "alpha": {"pacer": [pacer("2026-11-13T17:30:00Z", 0.07, ready=3, claims=2)], "reports": [report("2026-11-13T10:00:00Z", usd=3.0)],
                  "roadmap": "## 1. Goal\n- [x] `g:a` done\n- [ ] `g:b` open\n", "errors": [],
                  "waiting": [{"number": 7, "title": "Decide: a or b", "labels": ["for-lars"], "created_at": "2026-11-11T18:00:00Z"}]},
        "beta": {"pacer": [], "reports": [report("2026-11-13T12:00:00Z", lane="haiku", usd=1.0, session="s9")], "roadmap": None,
                 "waiting": None, "errors": ["issues: GitHub API 403 for /repos/g/beta/issues"]},
    }
    m = model.build(FLEET, loaded, NOW)
    alpha, beta = m["projects"]
    assert (alpha["share"], beta["share"]) == (0.75, 0.25)
    assert (alpha["done"], alpha["total"]) == (1, 2) and beta["goals"] is None and beta["waiting"] is None
    assert alpha["waiting"][0]["days"] == 2.0 and alpha["waiting"][0]["url"] == "https://github.com/g/alpha/issues/7"
    assert m["totals"] == {"done": 1, "total": 2, "waiting": 1, "ready": 3, "claims": 2, "prs_7d": 2, "usd_7d": 4.0}
    week = m["weeks"][-1]
    assert week["current"] and week["usd"] == 4.0 and set(week["split"]) == {"alpha", "beta"}
    assert [lane["lane"] for lane in m["lanes"]] == ["haiku", "main"]
    assert beta["errors"] and m["quota"]["seven_day"]["used"] == 0.07
