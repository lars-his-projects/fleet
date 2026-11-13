"""The person of a card is the assignee of its issue (`fleetpage/model.py`, `fleetpage/sources.py`)."""
import json

from fleetpage import model, sources

NOW = model.ts("2026-11-13T18:00:00Z")


def test_the_assignees_are_the_persons_of_a_card():
    card = {"title": "Decide: a or b", "labels": ["needs-human", "decision"], "assignees": ["zoe", {"login": "adam"}]}
    assert model.classify(card) == ("decision", ["adam", "zoe"])


def test_an_assignee_wins_over_the_old_label_and_the_old_label_still_shows_alone():
    both = {"title": "Check: x", "labels": ["for-lars"], "assignees": ["Jeroenvb3"]}
    assert model.classify(both) == ("check", ["Jeroenvb3"])
    assert model.classify({"title": "Check: x", "labels": ["for-lars"], "assignees": []}) == ("check", ["lars"])
    assert model.classify({"title": "Check: x", "labels": []}) == ("check", [])


def test_the_inbox_row_names_the_assignee():
    rows = model.waiting([{"number": 4, "title": "Step: y", "labels": ["step"], "assignees": ["zoe"],
                           "created_at": "2026-11-12T18:00:00Z"}], "g/alpha", NOW)
    assert rows[0]["for"] == ["zoe"] and rows[0]["days"] == 1.0


def test_the_read_of_the_issues_keeps_the_assignees(monkeypatch):
    issues = [{"number": 4, "title": "Step: y", "html_url": "u", "created_at": "2026-11-12T18:00:00Z",
               "labels": [{"name": "needs-human"}], "assignees": [{"login": "zoe"}]},
              {"number": 5, "title": "A pull request", "pull_request": {}, "labels": [], "assignees": []}]
    monkeypatch.setattr(sources, "get", lambda path, token=None: json.dumps(issues))
    got = sources.fetch_waiting("g/alpha")
    assert [(i["number"], i["assignees"], i["labels"]) for i in got] == [(4, ["zoe"], ["needs-human"])]
