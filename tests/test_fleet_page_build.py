"""The build command of the fleet page (`fleetpage/build.py`) with local files and no network."""
import json

from fleetpage import build, sources

RESET = 1795147200      # 2026-11-20T04:00:00Z
CONFIG = """
[fleet]
owner = "o"
org = "g"
[stages]
build = 1
[projects.alpha]
repo = "g/alpha"
stage = "build"
"""


def metrics(folder):
    (folder / "pacer").mkdir(parents=True)
    (folder / "runs" / "2026-11-13").mkdir(parents=True)
    record = {"at": "2026-11-13T17:30:00Z", "seven_day": [0.07, RESET, "allowed"], "five_hour": [0.2, RESET, "allowed"], "ready": 1, "claims": 0}
    (folder / "pacer" / "2026-11-13.jsonl").write_text(json.dumps(record) + "\nnot json\n\n[1, 2]\n")
    report = {"created_at": "2026-11-13T10:00:00Z", "tickets": [{"result": "pr #3"}], "tokens": {"usd": 1.5}, "body": "wall 8 min"}
    (folder / "runs" / "2026-11-13" / "1.json").write_text(json.dumps(report))
    (folder / "runs" / "2026-11-13" / "2.json").write_text("{broken")
    return folder


def test_read_metrics_skips_what_is_not_a_json_object(tmp_path):
    pacer, reports = sources.read_metrics(metrics(tmp_path / "m"))
    assert len(pacer) == 1 and len(reports) == 1
    assert sources.read_metrics(tmp_path / "missing") == ([], [])


def test_the_build_writes_the_page_and_the_data(tmp_path, capsys):
    (tmp_path / "fleet.toml").write_text(CONFIG)
    (tmp_path / "ROADMAP.md").write_text("## 1. Goal\n- [x] `g:a` done\n")
    (tmp_path / "issues.json").write_text(json.dumps({"alpha": [{"number": 4, "title": "Check: x", "labels": []}]}))
    code = build.main(["--out", str(tmp_path / "site"), "--config", str(tmp_path / "fleet.toml"), "--offline", "--now", "2026-11-13T18:00:00Z",
                       "--metrics-dir", f"alpha={metrics(tmp_path / 'm')}", "--roadmap", f"alpha={tmp_path / 'ROADMAP.md'}",
                       "--issues-json", str(tmp_path / "issues.json")])
    assert code == 0
    data = json.loads((tmp_path / "site" / "data.json").read_text())
    project = data["projects"][0]
    assert (project["done"], project["total"], project["prs_7d"], len(project["waiting"]), project["errors"]) == (1, 1, 1, 1, [])
    assert data["generated"] == "2026-11-13T18:00:00Z" and data["quota"]["seven_day"]["used"] == 0.07
    assert "alpha" in (tmp_path / "site" / "index.html").read_text()
    assert "alpha: 1 / 1 features" in capsys.readouterr().out


def test_offline_with_no_local_data_names_the_fault_and_still_builds(tmp_path):
    (tmp_path / "fleet.toml").write_text(CONFIG)
    assert build.main(["--out", str(tmp_path / "site"), "--config", str(tmp_path / "fleet.toml"), "--offline"]) == 0
    project = json.loads((tmp_path / "site" / "data.json").read_text())["projects"][0]
    assert project["errors"] == ["the metrics branch was not read (offline)"] and project["waiting"] is None


def test_a_fault_in_the_registry_stops_the_build(tmp_path, capsys):
    (tmp_path / "fleet.toml").write_text(CONFIG.replace('stage = "build"', 'stage = "later"'))
    assert build.main(["--out", str(tmp_path / "site"), "--config", str(tmp_path / "fleet.toml"), "--offline"]) == 1
    assert "stage must be one of" in capsys.readouterr().err and not (tmp_path / "site").exists()
