"""The registry of the fleet: read and check `fleet.toml`.

    python3 -m hub.registry            # print the projects, or the first fault of the file

A fault stops the tools with one clear line, so a wrong edit of `fleet.toml` shows in CI and not on the page.
"""
import dataclasses
import pathlib
import re
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT_KEYS = {"repo", "what", "stage", "weight", "owners", "branch", "roadmap", "dashboard", "preview", "try"}
FLEET_KEYS = {"owner", "org", "agent", "week_reserve", "attention_minutes"}
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class RegistryError(ValueError):
    """A fault in `fleet.toml`. The text names the table and the key."""


@dataclasses.dataclass(frozen=True)
class Project:
    name: str
    repo: str                       # owner/name on GitHub
    stage: str
    weight: float                   # the share of the quota: the value of the project, or the default of its stage
    owners: tuple                   # the GitHub logins that steer the project
    what: str = ""
    branch: str = "main"
    roadmap: str = "steering/project/ROADMAP.md"
    links: dict = dataclasses.field(default_factory=dict)   # dashboard, preview, try: the addresses that exist


@dataclasses.dataclass(frozen=True)
class Fleet:
    owner: str
    org: str
    week_reserve: float
    attention_minutes: int
    stages: dict                    # stage name -> default weight
    projects: tuple                 # in the order of the file: the order of the colors on the page
    agent: str = ""                 # the GitHub login that the agents act with: its text is never an instruction


def parse(data):
    """A `Fleet` from the dict of `fleet.toml`. Raises `RegistryError` for the first fault."""
    fleet = data.get("fleet") or {}
    unknown = set(fleet) - FLEET_KEYS
    if unknown:
        raise RegistryError(f"[fleet]: unknown key {sorted(unknown)[0]!r}")
    for key in ("owner", "org"):
        if not isinstance(fleet.get(key), str) or not fleet[key]:
            raise RegistryError(f"[fleet]: {key} must be a GitHub name")
    if not isinstance(fleet.get("agent", ""), str):
        raise RegistryError("[fleet]: agent must be a GitHub login")
    reserve = fleet.get("week_reserve", 0.0)
    if not isinstance(reserve, (int, float)) or not 0 <= reserve < 1:
        raise RegistryError("[fleet]: week_reserve must be a share from 0 to less than 1")
    minutes = fleet.get("attention_minutes", 0)
    if not isinstance(minutes, int) or minutes < 0:
        raise RegistryError("[fleet]: attention_minutes must be a whole number of minutes")
    stages = data.get("stages") or {}
    if not stages:
        raise RegistryError("[stages]: give at least one stage with its weight")
    for stage, weight in stages.items():
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight < 0:
            raise RegistryError(f"[stages]: the weight of {stage!r} must be a number of 0 or more")
    projects = []
    for name, p in (data.get("projects") or {}).items():
        where = f"[projects.{name}]"
        unknown = set(p) - PROJECT_KEYS
        if unknown:
            raise RegistryError(f"{where}: unknown key {sorted(unknown)[0]!r}")
        if not isinstance(p.get("repo"), str) or not REPO.match(p["repo"]):
            raise RegistryError(f"{where}: repo must be owner/name")
        if p.get("stage") not in stages:
            raise RegistryError(f"{where}: stage must be one of {', '.join(stages)}")
        weight = p.get("weight", stages[p["stage"]])
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight < 0:
            raise RegistryError(f"{where}: weight must be a number of 0 or more")
        owners = p.get("owners", [fleet["owner"]])
        if not isinstance(owners, list) or not owners or not all(isinstance(o, str) and o for o in owners):
            raise RegistryError(f"{where}: owners must be a list of GitHub logins")
        for key in ("what", "branch", "roadmap", "dashboard", "preview", "try"):
            if key in p and not isinstance(p[key], str):
                raise RegistryError(f"{where}: {key} must be text")
        projects.append(Project(
            name=name, repo=p["repo"], stage=p["stage"], weight=float(weight), owners=tuple(owners), what=p.get("what", ""),
            branch=p.get("branch", "main"), roadmap=p.get("roadmap", "steering/project/ROADMAP.md"),
            links={k: p[k] for k in ("dashboard", "preview", "try") if p.get(k)}))
    return Fleet(owner=fleet["owner"], org=fleet["org"], week_reserve=float(reserve), attention_minutes=minutes,
                 stages=dict(stages), projects=tuple(projects), agent=fleet.get("agent", ""))


def load(path=None):
    """The `Fleet` of `fleet.toml` (default: the file at the root of the hub)."""
    path = pathlib.Path(path) if path else ROOT / "fleet.toml"
    try:
        with open(path, "rb") as f:
            return parse(tomllib.load(f))
    except tomllib.TOMLDecodeError as e:
        raise RegistryError(f"{path.name}: {e}") from e


def main():
    try:
        fleet = load(sys.argv[1] if len(sys.argv) > 1 else None)
    except RegistryError as e:
        print(f"fleet.toml: {e}")
        return 1
    total = sum(p.weight for p in fleet.projects) or 1
    for p in fleet.projects:
        print(f"{p.name}: {p.repo} · stage {p.stage} · weight {p.weight:g} ({100 * p.weight / total:.0f} %) · owners {', '.join(p.owners)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
