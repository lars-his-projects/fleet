"""The reads of the fleet page: the `metrics` branch of a project (git), and its roadmap and waiting tickets (GitHub API).

The projects are public, so the reads work with no token. A token (`GITHUB_TOKEN`) only gives a higher API limit.
Each function returns plain data, or raises `SourceError` with one clear line.
"""
import json
import pathlib
import subprocess
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"


class SourceError(RuntimeError):
    """A read that failed. The page shows the text next to the project."""


def clone_metrics(repo, dest):
    """Clone the newest commit of the branch `metrics` of `repo` into `dest` and return `dest`."""
    r = subprocess.run(["git", "clone", "--quiet", "--depth", "1", "--single-branch", "--branch", "metrics",
                        f"https://github.com/{repo}.git", str(dest)], capture_output=True, text=True, timeout=300)
    if r.returncode:
        raise SourceError(f"no metrics branch: {(r.stderr.strip().splitlines() or ['git clone failed'])[-1]}")
    return pathlib.Path(dest)


def read_metrics(folder):
    """(pacer records, run reports) from the folders `pacer/` (one JSON object per line) and `runs/` (one JSON file per report).

    A line or a file that is not JSON is skipped: one bad record must not stop the page.
    """
    folder = pathlib.Path(folder)
    pacer, reports = [], []
    for path in sorted((folder / "pacer").glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip():
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if isinstance(record, dict):
                    pacer.append(record)
    for path in sorted((folder / "runs").rglob("*.json")):
        try:
            report = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except ValueError:
            continue
        if isinstance(report, dict):
            reports.append(report)
    return pacer, reports


def get(path, token=None, accept="application/vnd.github+json", timeout=30):
    """The body (bytes) of `GET https://api.github.com/<path>`."""
    request = urllib.request.Request(API + path, headers={"Accept": accept, "User-Agent": "fleet-page",
                                                         "X-GitHub-Api-Version": "2022-11-28"})
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as e:
        raise SourceError(f"GitHub API {e.code} for {path.split('?')[0]}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise SourceError(f"GitHub API not reachable: {getattr(e, 'reason', e)}") from e


def fetch_roadmap(repo, branch, path, token=None):
    """The text of the roadmap file of a project."""
    return get(f"/repos/{repo}/contents/{urllib.parse.quote(path)}?ref={urllib.parse.quote(branch)}", token,
               accept="application/vnd.github.raw+json").decode("utf-8", errors="replace")


def fetch_waiting(repo, token=None, pages=5):
    """The open issues of `repo` with the label `needs-human` (no pull requests), at most `pages` × 100."""
    issues = []
    for page in range(1, pages + 1):
        batch = json.loads(get(f"/repos/{repo}/issues?state=open&labels=needs-human&per_page=100&page={page}", token))
        issues += [{"number": i.get("number"), "title": i.get("title"), "html_url": i.get("html_url"),
                    "created_at": i.get("created_at"), "labels": [label.get("name", "") for label in i.get("labels") or []]}
                   for i in batch if "pull_request" not in i]
        if len(batch) < 100:
            break
    return issues
