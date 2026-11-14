"""The lane of each run at work on the fleet page, from the claim commits."""
import json

from fleetpage import build, model, page, sources
from tests.test_fleet_page_live import with_working
from tests.test_fleet_page_render import NOW, fleet


def test_lane_from_the_subject():
    assert model.claim_lane("Claim #5 by agent/5-x (u-1) lane haiku") == "haiku"
    assert model.claim_lane("Claim #5 by agent/5-x (u-1) lane fable") == "fable"
    assert model.claim_lane("Claim #5 by agent/5-x (u-1) lane main") == "opus"
    assert model.claim_lane("Claim #5 by agent/5-x (u-1)") == "opus"


def test_html_shows_lane_and_minutes_and_a_dash_without_claim():
    data = with_working()
    data["alpha"]["claims"] = {9: {"subject": "Claim #9 by b (u) lane sonnet", "date": "2026-11-13T17:40:00Z"}}
    html = page.render(model.build(fleet(), data, NOW))
    assert "<td>sonnet</td><td class=\"n\">20 min</td>" in html
    assert "<td>–</td><td class=\"n\">–</td>" in html


def _fake_get(refs, commits):
    def get(path, token=None, **kw):
        if "matching-refs" in path:
            return json.dumps(refs).encode()
        return json.dumps(commits[path.rsplit("/", 1)[1]]).encode()
    return get


def test_fetch_claims_takes_the_newest_ref_of_wanted_tickets(monkeypatch):
    refs = [{"ref": "refs/heads/claim/9", "object": {"sha": "a"}}, {"ref": "refs/heads/claim/9-2", "object": {"sha": "b"}},
            {"ref": "refs/heads/claim/4", "object": {"sha": "c"}}, {"ref": "refs/heads/claim/3", "object": {"sha": "d"}}]
    commits = {"a": {"message": "Claim #9 old", "committer": {"date": "2026-11-13T10:00:00Z"}},
               "b": {"message": "Claim #9 new lane haiku\n\nx", "committer": {"date": "2026-11-13T11:00:00Z"}},
               "d": {"message": "Release #3", "committer": {"date": "2026-11-13T11:00:00Z"}}}
    monkeypatch.setattr(sources, "get", _fake_get(refs, commits))
    assert sources.fetch_claims("g/a", [9, 3]) == {9: {"subject": "Claim #9 new lane haiku", "date": "2026-11-13T11:00:00Z"}}


def test_failed_read_adds_fault_and_runs_still_show(monkeypatch):
    p = fleet().projects[0]
    monkeypatch.setattr(sources, "clone_metrics", lambda *a: (_ for _ in ()).throw(sources.SourceError("no")))
    monkeypatch.setattr(sources, "fetch_roadmap", lambda *a, **k: "")
    monkeypatch.setattr(sources, "fetch_waiting", lambda *a, **k: [])
    monkeypatch.setattr(sources, "fetch_working", lambda *a, **k: [{"number": 9, "title": "t", "html_url": "u", "updated_at": "2026-11-13T17:30:00Z"}])

    def boom(*a, **k):
        raise sources.SourceError("GitHub API 500 for x")
    monkeypatch.setattr(sources, "fetch_claims", boom)
    data = build.load_project(p, None)
    assert any(e.startswith("claims: ") for e in data["errors"])
    rows = model.working(data["working"], p.repo, NOW, data["claims"])
    assert rows[0]["lane"] is None
