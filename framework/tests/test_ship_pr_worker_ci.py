"""framework/tools/ship_pr.py starts `ci.yml` on the branch when the push came from a job of GitHub Actions (hub #20).

A push and a PR with the token of a job start no `pull_request` workflow, so the PR of a worker run had no CI.
"""
import json

import dashboard
import ship_pr as ship
from test_ship_pr import fake_github, repo

DISPATCH = ("actions/workflows/ci.yml/dispatches", "POST", {"ref": "side"})


def test_a_push_from_a_job_starts_ci_on_the_branch(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(repo(tmp_path))
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    calls = fake_github(monkeypatch)
    monkeypatch.setattr(ship, "push", lambda n: True)
    (tmp_path / "body.md").write_text("What changed.")
    assert ship.main(["5", "--title", "T", "--body", str(tmp_path / "body.md"), "--tested"]) == 0
    assert DISPATCH in calls
    assert calls.index(DISPATCH) > next(i for i, c in enumerate(calls) if c[0] == "pulls" and c[1] == "POST")
    assert "started ci.yml on side" in capsys.readouterr().out


def test_a_later_push_from_a_job_starts_ci_again(tmp_path, monkeypatch):
    monkeypatch.chdir(repo(tmp_path))
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    calls = fake_github(monkeypatch, open_prs=[{"number": 9}])
    monkeypatch.setattr(ship, "push", lambda n: True)
    assert ship.main(["5", "--tested"]) == 0
    assert DISPATCH in calls


def test_a_push_from_a_session_starts_no_ci(tmp_path, monkeypatch):
    monkeypatch.chdir(repo(tmp_path))
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    calls = fake_github(monkeypatch, open_prs=[{"number": 9}])
    monkeypatch.setattr(ship, "push", lambda n: True)
    assert ship.main(["5", "--tested"]) == 0
    assert not [c for c in calls if c[0].startswith("actions/")]


def test_a_push_that_fails_starts_no_ci(tmp_path, monkeypatch):
    monkeypatch.chdir(repo(tmp_path))
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    calls = fake_github(monkeypatch)
    monkeypatch.setattr(ship, "push", lambda n: False)
    assert ship.main(["5", "--tested"]) == 3
    assert not [c for c in calls if c[0].startswith("actions/")]


def test_the_empty_answer_of_the_dispatch_is_no_error(monkeypatch, capsys):
    def api(path, method="GET", data=None):
        return json.loads("")                           # the answer 204 has no body
    monkeypatch.setattr(dashboard, "api", api)
    assert ship.start_ci("b", {"GITHUB_ACTIONS": "true"}) is True
    assert "started ci.yml on b" in capsys.readouterr().out


def test_a_refused_dispatch_names_the_next_step(monkeypatch, capsys):
    def api(path, method="GET", data=None):
        raise OSError("HTTP Error 403: Forbidden")
    monkeypatch.setattr(dashboard, "api", api)
    assert ship.start_ci("b", {"GITHUB_ACTIONS": "true"}) is False
    out = capsys.readouterr().out
    assert "403" in out and "ci.yml" in out
