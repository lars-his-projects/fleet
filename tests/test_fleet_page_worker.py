"""The state of the worker on the fleet page: online, offline, no file, a bad file."""
import json

from fleetpage import build, model, page, sources
from tests.test_fleet_page_render import NOW, fleet, loaded


def beat(time, name="polopc", **extra):
    return {"worker": name, "time": time, **extra}


def test_fresh_record_is_online():
    rows = model.worker_state([beat("2026-11-13T17:40:00Z", kvm=True)], NOW)
    assert rows[0]["online"] is True and rows[0]["minutes"] == 20 and rows[0]["kvm"] is True


def test_old_record_is_offline():
    assert model.worker_state([beat("2026-11-13T15:00:00Z")], NOW)[0]["online"] is False


def test_newest_record_wins_and_bad_records_are_skipped():
    rows = model.worker_state([beat("2026-11-13T10:00:00Z"), beat("2026-11-13T17:50:00Z"), {"worker": "x"},
                               {"time": "2026-11-13T17:50:00Z"}, beat("nonsense"), {"worker": 5, "time": None}], NOW)
    assert [(r["name"], r["online"]) for r in rows] == [("polopc", True)]


def test_page_shows_online_and_offline_with_escaped_name():
    data = loaded()
    data["alpha"]["workers"] = [beat("2026-11-13T17:50:00Z"), beat("2026-11-13T09:00:00Z", name="<i>old</i>")]
    html = page.render(model.build(fleet(), data, NOW))
    assert "<b>polopc</b>: online, last job" in html
    assert "&lt;i&gt;old&lt;/i&gt;</b>: offline" in html
    assert "<i>old</i>" not in html


def test_no_heartbeat_shows_text_and_rest_of_page():
    html = page.render(model.build(fleet(), loaded(), NOW))
    assert "Worker: no heartbeat." in html
    assert "Runs at work" in html


def test_read_workers_skips_bad_file(tmp_path):
    (tmp_path / "worker").mkdir()
    (tmp_path / "worker" / "a.json").write_text(json.dumps(beat("2026-11-13T17:50:00Z")))
    (tmp_path / "worker" / "b.json").write_text("{not json")
    assert sources.read_workers(tmp_path) == [beat("2026-11-13T17:50:00Z")]
    assert sources.read_workers(tmp_path / "none") == []


def test_load_project_reads_workers(tmp_path):
    (tmp_path / "worker").mkdir()
    (tmp_path / "worker" / "a.json").write_text(json.dumps(beat("2026-11-13T17:50:00Z")))
    data = build.load_project(fleet().projects[0], None, metrics_dir=tmp_path, offline=True)
    assert data["workers"][0]["worker"] == "polopc"
