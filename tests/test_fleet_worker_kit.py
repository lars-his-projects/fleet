"""The kit of the fleet worker on polopc (`deploy/worker/`): the form of its files and the behavior of `entrypoint.sh`.

No test reads a value of a configuration file. PyYAML is not a dependency, so a small reader takes the parts of the
compose file and of the workflows that the checks need.
"""
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
KIT = ROOT / "deploy" / "worker"
ENTRY = KIT / "entrypoint.sh"
WORKFLOWS = ROOT / ".github" / "workflows"
BASH = shutil.which("bash")
LABEL = "polopc"
FORBIDDEN = {"pull_request", "pull_request_target"}
VARS = {"ACCESS_TOKEN": "secret-token-123", "ORG": "o", "RUNNER_NAME": "r", "LABELS": "l"}

FAKE_CURL = """#!/usr/bin/env bash
cat > /dev/null
out=""
while [[ $# -gt 0 ]]; do
  if [[ "$1" == "-o" ]]; then out="$2"; shift; fi
  shift
done
printf '%s' "$FAKE_BODY" > "$out"
printf '%s' "$FAKE_STATUS"
"""


def _script(path, text):
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def run_entry(tmp_path, env, status="201", body='{"token": "reg-456"}'):
    """Run entrypoint.sh with a fake curl on PATH and a fake runner in HOME."""
    bindir = tmp_path / "bin"
    home = tmp_path / "home"
    bindir.mkdir(exist_ok=True)
    home.mkdir(exist_ok=True)
    _script(bindir / "curl", FAKE_CURL)
    _script(home / "config.sh", '#!/usr/bin/env bash\nprintf "%s\\n" "$@" > "$HOME/config.args"\n')
    _script(home / "run.sh", '#!/usr/bin/env bash\nenv > "$HOME/run.env"\n')
    (home / "_work").mkdir(exist_ok=True)
    (home / ".runner").write_text("{}")
    full = {"PATH": f"{bindir}:/usr/bin:/bin", "HOME": str(home), "TMPDIR": str(tmp_path), "FAKE_STATUS": status, "FAKE_BODY": body, **env}
    res = subprocess.run([BASH, str(ENTRY)], env=full, capture_output=True, text=True, timeout=30)
    return res, home


def env_example_names():
    return {line.split("=", 1)[0].strip() for line in (KIT / ".env.example").read_text().splitlines()
            if "=" in line and not line.lstrip().startswith("#")}


def blocks(text, indent):
    """The keys at one indent level of a YAML text, each with the lines below it (comments removed)."""
    out, key = {}, None
    for raw in text.splitlines():
        line = raw.split(" #")[0].rstrip() if not raw.lstrip().startswith("#") else ""
        if not line.strip():
            continue
        pad = len(line) - len(line.lstrip())
        if pad < indent:
            key = None
        elif pad == indent and re.match(r"^\s*[\w.-]+:", line):
            key = line.strip().split(":", 1)[0]
            out[key] = [line.strip()]
        elif key:
            out[key].append(line.strip())
    return out


def _services(text):
    lines = text.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.rstrip() == "services:")
    end = next((i for i in range(start + 1, len(lines)) if lines[i] and not lines[i][0].isspace()
                and not lines[i].startswith("#")), len(lines))
    return blocks("\n".join(lines[start + 1:end]), 2)


def volume_sources(lines):
    """The source of each entry of the `volumes:` list of one service."""
    out, inside = [], False
    for ln in lines[1:]:
        if ln.endswith(":") and not ln.startswith("-"):
            inside = ln == "volumes:"
            continue
        if inside and ln.startswith("- "):
            out.append(ln[2:].strip().strip("\"'").split(":", 1)[0])
        elif inside and not ln.startswith("-"):
            inside = False
    return out


def triggers(text):
    """The names of the events in the `on:` key of a workflow."""
    for ln in text.splitlines():
        m = re.match(r"^(on|\"on\"|'on'|true):\s*(.*)$", ln)
        if m:
            rest = m.group(2).split(" #")[0].strip()
            if rest:
                return {t.strip() for t in rest.strip("[]").split(",") if t.strip()}
            break
    else:
        return set()
    names, seen = set(), False
    for ln in text.splitlines():
        if re.match(r"^(on|\"on\"|'on'|true):", ln):
            seen = True
            continue
        if seen:
            if ln and not ln[0].isspace() and not ln.startswith("#"):
                break
            m = re.match(r"^  ([\w-]+):", ln)
            if m:
                names.add(m.group(1))
    return names


def test_entrypoint_syntax():
    subprocess.run([BASH, "-n", str(ENTRY)], check=True)


def test_entrypoint_stops_with_an_empty_environment():
    res = subprocess.run([BASH, str(ENTRY)], env={}, capture_output=True, text=True, timeout=30)
    assert res.returncode != 0
    assert "ACCESS_TOKEN" in res.stderr and "not set" in res.stderr


@pytest.mark.parametrize("name", sorted(VARS))
def test_entrypoint_names_each_missing_variable(tmp_path, name):
    env = {k: v for k, v in VARS.items() if k != name}
    res, home = run_entry(tmp_path, env)
    assert res.returncode != 0
    assert name in res.stderr
    assert not (home / "config.args").exists()


def test_entrypoint_shows_the_http_status_and_never_the_token(tmp_path):
    res, home = run_entry(tmp_path, VARS, status="401", body='{"message": "Bad credentials"}')
    assert res.returncode != 0
    assert "HTTP 401" in res.stderr
    assert VARS["ACCESS_TOKEN"] not in res.stdout + res.stderr
    assert not (home / "config.args").exists()


def test_entrypoint_stops_when_the_answer_has_no_token(tmp_path):
    res, home = run_entry(tmp_path, VARS, body="{}")
    assert res.returncode != 0
    assert not (home / "config.args").exists()


def test_entrypoint_registers_an_ephemeral_runner_without_the_access_token(tmp_path):
    res, home = run_entry(tmp_path, VARS)
    assert res.returncode == 0, res.stderr
    args = (home / "config.args").read_text().split("\n")
    for flag in ("--unattended", "--ephemeral", "--replace"):
        assert flag in args
    assert args[args.index("--token") + 1] == "reg-456"
    assert args[args.index("--name") + 1] == VARS["RUNNER_NAME"]
    assert args[args.index("--labels") + 1] == VARS["LABELS"]
    assert args[args.index("--url") + 1].endswith("/" + VARS["ORG"])
    run_env = (home / "run.env").read_text()
    assert "ACCESS_TOKEN" not in run_env and VARS["ACCESS_TOKEN"] not in run_env
    assert not (home / "_work").exists() and not (home / ".runner").exists()


def test_each_variable_of_the_entrypoint_is_in_env_example():
    text = "\n".join(ln for ln in ENTRY.read_text().splitlines() if not ln.lstrip().startswith("#"))
    used = set(re.findall(r"\$\{?([A-Z][A-Z0-9_]*)", text)) | set(re.findall(r"\bfor name in ([A-Z_ ]+);", text)[0].split())
    used -= {"HOME", "PATH"}
    assert used, "the reader found no variable in entrypoint.sh"
    assert used <= env_example_names(), used - env_example_names()


def test_env_example_has_a_comment_line_per_variable():
    lines = (KIT / ".env.example").read_text().splitlines()
    for i, line in enumerate(lines):
        if "=" in line and not line.startswith("#"):
            assert i > 0 and lines[i - 1].startswith("# "), f"no comment above {line.split('=')[0]}"


def test_compose_parses_as_yaml_when_pyyaml_is_there():
    yaml = pytest.importorskip("yaml")
    data = yaml.safe_load((KIT / "docker-compose.yml").read_text())
    assert set(data["services"]) == set(_services((KIT / "docker-compose.yml").read_text()))


def test_compose_isolates_the_worker():
    svc = _services((KIT / "docker-compose.yml").read_text())
    assert "worker" in svc and "watchtower" in svc
    for name, lines in svc.items():
        body = "\n".join(lines)
        assert not re.search(r"privileged:\s*true", body), name
        assert not re.search(r"network_mode:\s*\"?host", body), name
        assert not re.search(r"pid:\s*\"?host", body), name
        assert "type: bind" not in body, name
        for src in volume_sources(lines):
            if name == "watchtower" and src == "/var/run/docker.sock":
                continue
            assert not src.startswith(("/", ".", "~", "$")), f"{name} mounts the host path {src}"
        if name != "watchtower":
            assert "docker.sock" not in body, f"{name} mounts the Docker socket"


def test_reader_sees_a_host_mount():
    sample = "services:\n  bad:\n    image: x\n    volumes:\n      - /home/lars:/data\n      - named:/v\n"
    assert volume_sources(_services(sample)["bad"]) == ["/home/lars", "named"]


@pytest.mark.parametrize("text,want", [
    ("on:\n  workflow_dispatch:\n  pull_request:\n    branches: [main]\njobs:\n", {"workflow_dispatch", "pull_request"}),
    ("on: [push, pull_request_target]\n", {"push", "pull_request_target"}),
    ("on: pull_request\n", {"pull_request"}),
])
def test_trigger_reader(text, want):
    assert triggers(text) == want


def test_no_polopc_workflow_runs_on_a_pull_request():
    found = []
    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        code = "\n".join(ln.split(" #")[0] for ln in path.read_text().splitlines() if not ln.lstrip().startswith("#"))
        if LABEL in code:
            found.append(path.name)
            assert not triggers(path.read_text()) & FORBIDDEN, f"{path.name} runs on polopc for a pull request"
    assert found, "no workflow uses the label polopc"

