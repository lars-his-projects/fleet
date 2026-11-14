"""framework/tools/usage.py: the work of an owner goes above the weekly pace, and `refill_roadmap = false` starts no
refill run for the roadmap. The owner answered 8 tickets of a paced project and no run used the answers for 4 hours
(travel-aggregator, 2026-11-14). A project with no weekly limit and no roadmap refill started an empty run each cycle
(the hub, the same day)."""
import dashboard
import feedback
import health
import usage

NOW = 1_800_000_000
H = 3600
FIVE = {"five_hour": (0.3, NOW + 2 * H, "allowed")}
AHEAD = FIVE | {"seven_day": (0.52, NOW + 145 * H, "allowed")}          # 52 % used after 23 of 168 hours
PACE = dict(burn7=0.0053, free7=0, week=True, hi=99, share7=1, reserve7=0)


def test_a_week_ahead_gives_a_run_for_the_work_of_an_owner(monkeypatch):
    monkeypatch.setattr(usage, "OWNER_FIRST", 2)
    assert usage.target_runs(AHEAD, NOW, **PACE) == 0
    assert usage.target_runs(AHEAD, NOW, owner=1, **PACE) == 1
    assert usage.target_runs(AHEAD, NOW, owner=5, **PACE) == 2          # not more than the setting
    monkeypatch.setattr(usage, "OWNER_FIRST", 0)                        # the setting 0: the weekly pace decides alone
    assert usage.target_runs(AHEAD, NOW, owner=1, **PACE) == 0


def test_the_work_of_an_owner_is_read_only_when_the_week_gives_no_run(monkeypatch):
    monkeypatch.setattr(usage, "OWNER_FIRST", 1)
    calls = []
    behind = FIVE | {"seven_day": (0.2, NOW + 4 * 86400, "allowed")}    # 20 % used after 43 % of the week

    def owner():
        calls.append(1)
        return 1
    assert usage.target_runs(behind, NOW, owner=owner, **PACE) == usage.target_runs(behind, NOW, **PACE) > 1
    assert not calls
    assert usage.target_runs(AHEAD, NOW, owner=owner, **PACE) == 1 and calls == [1]


def test_a_rejected_limit_stays_at_no_run(monkeypatch):
    monkeypatch.setattr(usage, "OWNER_FIRST", 1)
    assert usage.target_runs(AHEAD | {"seven_day": (1.0, NOW + H, "rejected")}, NOW, owner=1, **PACE) == 0
    assert usage.target_runs({"five_hour": (1.0, NOW + 600, "rejected")}, NOW, owner=1, **PACE) == 0


def test_owner_wait_counts_a_comment_with_no_answer_and_an_issue_with_no_label(monkeypatch):
    def wait():
        usage.owner_wait.cache_clear()
        try:
            return usage.owner_wait()
        finally:
            usage.owner_wait.cache_clear()
    pull = {"number": 4, "labels": [], "pull_request": {}}
    monkeypatch.setattr(dashboard, "pages", lambda path: [{"number": 3, "labels": [{"name": "P2"}]}, pull])
    monkeypatch.setattr(feedback, "fetch", lambda: [{"id": 1}])
    assert wait() == 1                                                   # a comment of an owner with no answer
    monkeypatch.setattr(feedback, "fetch", lambda: [])
    assert wait() == 0                                                   # a PR with no label is no new ticket
    monkeypatch.setattr(dashboard, "pages", lambda path: [{"number": 3, "labels": []}, pull])
    assert wait() == 1                                                   # a new issue that no run triaged

    def fail():
        raise OSError("no network")
    monkeypatch.setattr(feedback, "fetch", fail)
    assert wait() == 0                                                   # a read error: the weekly pace decides


def project(monkeypatch, issues=()):
    """A false project for `usage.fire`: the open issues `issues`, no claim, the lane `haiku`."""
    monkeypatch.setattr(dashboard, "RESERVED", ("haiku",))
    monkeypatch.setattr(dashboard, "pages", lambda path, limit=10: list(issues) if path.startswith("issues") else [])
    monkeypatch.setattr(dashboard, "api", lambda path, method="GET", data=None, repo=None: {"total_count": 0})
    monkeypatch.setattr(health, "claim_refs", lambda remote="origin": [])
    monkeypatch.setattr(health, "lane_weights", lambda comments: ({"haiku": 0.25}, {"haiku": "start"}))
    monkeypatch.setattr(usage, "due_reviews", lambda **_: [])
    monkeypatch.setattr(usage, "release_due", lambda: [])
    monkeypatch.setattr(usage, "free_sources", lambda *a, **k: [])


def test_the_run_above_the_weekly_pace_is_an_opus_run_also_with_no_ready_ticket(monkeypatch):
    haiku = {"number": 5, "title": "Ticket 5", "body": "", "created_at": "2020-01-01T00:00:00Z",
             "labels": [{"name": "P1"}, {"name": "lane:haiku"}]}
    waits = {"owner": 1}
    # the week gives no run; the work of an owner gives the runs of `owner`
    monkeypatch.setattr(usage, "target_runs", lambda u, now, burn=0, burn7=None, owner=0, **k: owner() if callable(owner) else owner)
    monkeypatch.setattr(usage, "owner_wait", lambda: waits["owner"])
    five = {"five_hour": (0.2, NOW + 3 * H, "allowed")}
    project(monkeypatch)                                                 # nothing is ready
    k, runs, line = usage.fire(five, NOW, status=([], ""))
    assert (k, runs["haiku"]) == (1, 0) and "owner first" in line
    project(monkeypatch, [haiku])                                        # a ticket of a lane is ready: still an Opus run
    k, runs, _ = usage.fire(five, NOW, status=([], ""))
    assert (k, runs["haiku"]) == (1, 0)
    k, runs, _ = usage.fire(five, NOW, status=([], ""), started={"main": 1})   # the run of the cycle before has no claim yet
    assert k == 0
    waits["owner"] = 0                                                   # no work of an owner: the week decides
    k, runs, line = usage.fire(five, NOW, status=([], ""))
    assert (k, runs["haiku"]) == (0, 0) and "owner first" not in line


def test_the_roadmap_starts_no_refill_run_when_the_setting_is_off(monkeypatch):
    """Nothing is ready, and the roadmap has features with no epic."""
    project(monkeypatch)
    monkeypatch.setattr(usage, "free_sources", lambda *a, **k: ["3 roadmap features with no epic"])
    monkeypatch.setattr(usage, "refill_runs", lambda issues, now: 1)

    def fire():
        return usage.fire({"five_hour": (0.2, NOW + 3 * H, "allowed")}, NOW, status=([], ""), target=4)
    monkeypatch.setattr(usage, "ROADMAP_REFILL", True)
    k, _, line = fire()
    assert k == 1 and "3 roadmap features with no epic" in line
    monkeypatch.setattr(usage, "ROADMAP_REFILL", False)
    k, _, line = fire()
    assert k == 0 and "refill 0 " in line
