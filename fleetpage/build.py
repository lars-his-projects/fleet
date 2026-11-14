"""Build the fleet page: read each project of `fleet.toml`, write `index.html` and `data.json`.

    python3 -m fleetpage.build --out _site
    python3 -m fleetpage.build --out _site --metrics-dir aoe2mc=/path/to/a/checkout/of/its/metrics/branch
    python3 -m fleetpage.build --out _site --offline        # no network: only the folders of --metrics-dir

The workflow `fleet-page.yml` runs the first form. A read that fails does not stop the build: the page names the
project and the fault, and shows the other projects. The exit code is 1 only when `fleet.toml` has a fault.
"""
import argparse
import datetime
import json
import os
import pathlib
import sys
import tempfile

from fleetpage import model, page, sources
from hub import registry


def load_project(project, token, metrics_dir=None, offline=False, issues=None, roadmaps=None):
    """The loaded data of one project for `model.build()`. Each read that fails adds one line to `errors`."""
    data = {"pacer": [], "reports": [], "roadmap": None, "waiting": None, "working": None, "workers": [], "errors": []}
    with tempfile.TemporaryDirectory() as tmp:
        try:
            folder = metrics_dir or (None if offline else sources.clone_metrics(project.repo, pathlib.Path(tmp) / "metrics"))
            if folder:
                data["pacer"], data["reports"] = sources.read_metrics(folder)
                data["workers"] = sources.read_workers(folder)
            else:
                data["errors"].append("the metrics branch was not read (offline)")
        except (sources.SourceError, OSError) as e:
            data["errors"].append(str(e))
    if roadmaps and project.name in roadmaps:
        data["roadmap"] = pathlib.Path(roadmaps[project.name]).read_text(encoding="utf-8")
    elif not offline:
        try:
            data["roadmap"] = sources.fetch_roadmap(project.repo, project.branch, project.roadmap, token)
        except sources.SourceError as e:
            data["errors"].append(f"roadmap: {e}")
    if issues is not None:
        data["waiting"] = issues.get(project.name, [])
    elif not offline:
        try:
            data["waiting"] = sources.fetch_waiting(project.repo, token)
        except sources.SourceError as e:
            data["errors"].append(f"issues: {e}")
        try:
            data["working"] = sources.fetch_working(project.repo, token)
        except sources.SourceError as e:
            data["errors"].append(f"working: {e}")
    return data


def pairs(values):
    """{name: path} from `NAME=PATH` arguments."""
    out = {}
    for value in values or []:
        name, _, path = value.partition("=")
        if not name or not path:
            raise SystemExit(f"expected NAME=PATH, got {value!r}")
        out[name] = path
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default="_site", help="the folder for index.html and data.json")
    parser.add_argument("--config", help="the registry file (default: fleet.toml of the hub)")
    parser.add_argument("--metrics-dir", action="append", metavar="NAME=PATH", help="a local checkout of the metrics branch of a project")
    parser.add_argument("--roadmap", action="append", metavar="NAME=PATH", help="a local roadmap file of a project")
    parser.add_argument("--issues-json", help="a file {project: [issues]} in place of the GitHub API")
    parser.add_argument("--offline", action="store_true", help="make no network request")
    parser.add_argument("--now", help="the build time as 2026-11-13T18:00:00Z (default: the clock)")
    args = parser.parse_args(argv)
    try:
        fleet = registry.load(args.config)
    except registry.RegistryError as e:
        print(f"fleet.toml: {e}", file=sys.stderr)
        return 1
    now = model.ts(args.now) if args.now else datetime.datetime.now(model.UTC)
    token = os.environ.get("GITHUB_TOKEN") or None
    folders, roadmaps = pairs(args.metrics_dir), pairs(args.roadmap)
    issues = json.loads(pathlib.Path(args.issues_json).read_text(encoding="utf-8")) if args.issues_json else None
    loaded = {p.name: load_project(p, token, folders.get(p.name), args.offline, issues, roadmaps) for p in fleet.projects}
    m = model.build(fleet, loaded, now)
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page.render(m), encoding="utf-8")
    (out / "data.json").write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8")
    for p in m["projects"]:
        faults = f" · faults: {'; '.join(p['errors'])}" if p["errors"] else ""
        print(f"{p['name']}: {p['done']} / {p['total']} features · {len(p['waiting'] or [])} waiting · {p['prs_7d']} PRs in 7 days{faults}")
    print(f"wrote {out / 'index.html'} and {out / 'data.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
