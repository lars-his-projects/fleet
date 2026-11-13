"""The HTML of the fleet page (`fleetpage/page.py`): complete, balanced, and safe for text from outside."""
import re

from fleetpage import model, page
from hub import registry

NOW = model.ts("2026-11-13T18:00:00Z")
RESET = int(model.ts("2026-11-20T04:00:00Z").timestamp())
TAGS = ("div", "section", "table", "thead", "tbody", "tr", "td", "th", "article", "details", "svg", "span", "p", "h2", "h3", "h4", "a")


def fleet(names=("alpha", "beta")):
    return registry.parse({"fleet": {"owner": "o", "org": "g", "week_reserve": 0.1, "attention_minutes": 30}, "stages": {"build": 1},
                           "projects": {n: {"repo": f"g/{n}", "stage": "build", "what": f"What {n} does."} for n in names}})


def loaded():
    record = {"at": "2026-11-13T17:30:00Z", "seven_day": [0.07, RESET, "allowed"], "five_hour": [0.2, RESET - 3600, "allowed"],
              "target": 4, "ready": 1, "claims": 2, "problems": [], "line": "paused False"}
    old = dict(record, at="2026-11-12T09:30:00Z", seven_day=[0.99, RESET - model.WEEK, "allowed"])
    reports = [{"created_at": "2026-11-13T10:00:00Z", "lane": "opus", "session": "s1", "tokens": {"usd": 2.0},
                "tickets": [{"result": "pr #5"}], "body": "wall 10 min"}]
    return {
        "alpha": {"pacer": [record, old], "reports": reports, "roadmap": "## 1. Goal <one>\n- [x] `g:a` done\n- [ ] `g:b` open\n", "errors": [],
                  "waiting": [{"number": 7, "title": "Decide: <script>alert(1)</script> & more", "labels": ["for-lars"],
                               "created_at": "2026-11-11T18:00:00Z"}]},
        "beta": {"pacer": [], "reports": [], "roadmap": None, "waiting": None, "errors": ["no metrics branch: <fatal>"]},
    }


def balanced(text):
    return [tag for tag in TAGS if len(re.findall(rf"<{tag}[\s>]", text)) != len(re.findall(rf"</{tag}>", text))]


def test_the_page_shows_each_project_and_its_numbers():
    text = page.render(model.build(fleet(), loaded(), NOW))
    assert text.startswith("<!doctype html>") and "<title>Fleet</title>" in text
    for needle in ("alpha", "beta", "What alpha does.", "1 / 2", "This week", "Week of 6 Nov", "data.json", "30 minutes per week"):
        assert needle in text, needle
    assert balanced(text) == []


def test_text_from_outside_is_escaped():
    text = page.render(model.build(fleet(), loaded(), NOW))
    assert "<script>alert(1)</script>" not in text and "&lt;script&gt;alert(1)&lt;/script&gt; &amp; more" in text
    assert "Goal &lt;one&gt;" in text and "no metrics branch: &lt;fatal&gt;" in text


def test_a_fleet_with_no_data_still_gives_a_page():
    empty = {name: {"pacer": [], "reports": [], "roadmap": None, "waiting": None, "errors": []} for name in ("alpha", "beta")}
    text = page.render(model.build(fleet(), empty, NOW))
    assert "No pacer record" in text and "No run report yet" in text and balanced(text) == []
    assert balanced(page.render(model.build(fleet(names=()), {}, NOW))) == []


def test_a_caution_shows_when_the_pacer_records_are_old():
    late = model.ts("2026-11-13T20:00:00Z")
    assert "CAUTION" in page.render(model.build(fleet(), loaded(), late))
    assert "CAUTION" not in page.render(model.build(fleet(), loaded(), NOW))


def test_more_projects_than_colors_get_the_neutral_color():
    names = tuple(f"p{i}" for i in range(page.HUES + 2))
    empty = {name: {"pacer": [], "reports": [], "roadmap": "## 1. G\n- [x] `g:a` x\n", "waiting": [], "errors": []} for name in names}
    text = page.render(model.build(fleet(names), empty, NOW))
    assert f"var(--p{page.HUES - 1})" in text and f"var(--p{page.HUES})" not in text and "var(--muted)" in text


def test_ago_gives_minutes_hours_and_days():
    assert [page.ago(m) for m in (None, 12, 200, 5000)] == ["–", "12 min", "3 h", "3 days"]
