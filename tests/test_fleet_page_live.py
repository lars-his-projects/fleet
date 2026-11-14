"""The runs at work on the fleet page: each `in-progress` ticket of each project."""
import json

from fleetpage import build, model, page, sources
from tests.test_fleet_page_render import NOW, fleet, loaded


def with_working():
    data = loaded()
    data["alpha"]["working"] = [
        {"number": 9, "title": "Fix <b>x</b> & y", "html_url": "https://github.com/g/alpha/issues/9", "updated_at": "2026-11-13T17:30:00Z"},
        {"number": 3, "title": "Older", "html_url": "https://github.com/g/alpha/issues/3", "updated_at": "2026-11-13T16:00:00Z"}]
    data["beta"]["working"] = [{"number": 5, "title": "Beta job", "html_url": "https://github.com/g/beta/issues/5", "updated_at": "2026-11-13T17:59:00Z"}]
    return data


def test_each_run_at_work_shows_with_link_and_escaped_title():
    html = page.render(model.build(fleet(), with_working(), NOW))
    assert '<a href="https://github.com/g/alpha/issues/9">#9</a> Fix &lt;b&gt;x&lt;/b&gt; &amp; y' in html
    assert "<b>x</b>" not in html
    assert 'href="https://github.com/g/beta/issues/5">#5</a> Beta job' in html


def test_a_failed_read_names_the_project_and_shows_the_other_runs():
    data = with_working()
    data["beta"]["working"] = None
    html = page.render(model.build(fleet(), data, NOW))
    assert "Not read: beta." in html
    assert "#9</a>" in html


def test_model_gives_minutes_from_now_sorted_by_number():
    rows = model.build(fleet(), with_working(), NOW)["projects"][0]["working"]
    assert [r["number"] for r in rows] == [3, 9]
    assert [r["minutes"] for r in rows] == [120, 30]


def test_offline_load_gives_none(tmp_path):
    p = fleet().projects[0]
    assert build.load_project(p, None, offline=True)["working"] is None


def test_fetch_working_skips_pull_requests(monkeypatch):
    batch = [{"number": 1, "title": "a", "html_url": "u", "updated_at": "t", "labels": [{"name": "in-progress"}]},
             {"number": 2, "pull_request": {}}]
    monkeypatch.setattr(sources, "get", lambda path, token=None, **kw: json.dumps(batch).encode())
    assert [i["number"] for i in sources.fetch_working("g/a")] == [1]
