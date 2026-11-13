"""framework/tools/claim.py `--prune` in a repository with no claim ref (a new project): nothing to delete, and no git
error. `git fetch --depth 1` of a pattern that matches no ref exits 1, so the workflow Claims was red on each closed
issue of the hub (2026-11-13)."""
import subprocess

import claim
from test_claim import clones  # noqa: F401  (fixture)


def git(d, *args):
    return subprocess.run(["git", *args], cwd=d, capture_output=True, text=True, check=True).stdout


def commit(d, text):
    (d / "file.txt").write_text(text)
    git(d, "add", "file.txt")
    git(d, "commit", "-q", "-m", text)


def test_prune_with_no_claim_ref_deletes_nothing(clones, monkeypatch):  # noqa: F811
    a, _, _ = clones
    commit(a, "start")
    git(a, "push", "-q", "origin", "HEAD:refs/heads/main")      # the remote has a branch, but no claim ref
    monkeypatch.chdir(a)
    assert claim.prune(open_numbers={1}) == []


def test_prune_deletes_the_claim_of_a_closed_ticket_and_keeps_an_open_one(clones, monkeypatch):  # noqa: F811
    a, _, _ = clones
    commit(a, "start")
    for number in (12, 13):
        git(a, "push", "-q", "origin", f"HEAD:refs/heads/claim/{number}")
    monkeypatch.chdir(a)
    assert claim.prune(open_numbers={13}) == ["12"]
    assert [line.split("/")[-1] for line in git(a, "ls-remote", "--heads", "origin", "claim/*").splitlines()] == ["13"]
