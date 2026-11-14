"""`deploy/worker/install.sh`: the one command of the owner that installs the fleet worker (false docker and curl)."""
import shutil
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KIT = ROOT / "deploy" / "worker"
INSTALL = KIT / "install.sh"
BASH = shutil.which("bash")
TOKEN = "github_pat_Test_123"
TOOLS = ("bash", "mkdir", "chmod", "grep", "sed", "cat", "stat", "rm", "cp", "basename")   # what the scripts call

FAKE_CURL = """#!/usr/bin/env bash
# curl -fsSL -o FILE URL: copy the file of the kit with the name of the URL.
out=""; url=""
while [[ $# -gt 0 ]]; do
  case "$1" in -o) out="$2"; shift ;; -*) ;; *) url="$1" ;; esac
  shift
done
cp "$FAKE_SRC/$(basename "$url")" "$out"
"""
FAKE_DOCKER = """#!/usr/bin/env bash
echo "$*" >> "$FAKE_LOG"
"""


def script(path, text):
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def install(tmp_path, kvm=True, token=TOKEN, docker=True):
    """Run install.sh in a false home. Returns (result, the worker folder, the calls of docker)."""
    bindir, home = tmp_path / "bin", tmp_path / "home"
    bindir.mkdir(exist_ok=True)
    home.mkdir(exist_ok=True)
    for tool in TOOLS:                                    # only these programs: no real docker of the machine
        if not (bindir / tool).exists():
            (bindir / tool).symlink_to(shutil.which(tool))
    script(bindir / "curl", FAKE_CURL)
    if docker:
        script(bindir / "docker", FAKE_DOCKER)
    device = tmp_path / "kvm"
    if kvm:
        device.write_text("")
    log = tmp_path / "docker.log"
    env = {"PATH": str(bindir), "HOME": str(home), "FAKE_SRC": str(KIT), "FAKE_LOG": str(log),
           "FLEET_WORKER_KVM": str(device), "FLEET_WORKER_TOKEN": token}
    res = subprocess.run([BASH, str(INSTALL)], env=env, capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL)
    return res, home / "fleet-worker", log.read_text().splitlines() if log.exists() else []


def test_the_script_has_no_syntax_fault():
    assert subprocess.run([BASH, "-n", str(INSTALL)], capture_output=True).returncode == 0


def test_the_install_writes_the_token_and_starts_the_stack(tmp_path):
    res, folder, calls = install(tmp_path)
    assert res.returncode == 0, res.stderr
    env = folder / ".env"
    assert f"ACCESS_TOKEN={TOKEN}" in env.read_text().splitlines()
    assert stat.S_IMODE(env.stat().st_mode) == 0o600
    assert (folder / "docker-compose.yml").read_text() == (KIT / "docker-compose.yml").read_text()
    assert calls[-2:] == ["compose pull", "compose up -d"]
    assert TOKEN not in res.stdout + res.stderr


def test_the_worker_gets_the_emulator_device_only_when_the_computer_has_it(tmp_path):
    res, folder, _ = install(tmp_path, kvm=True)
    override = (folder / "docker-compose.override.yml").read_text()
    assert str(tmp_path / "kvm") in override and "group_add" in override
    (tmp_path / "kvm").unlink()                                   # the same folder, the device is gone
    res, folder, _ = install(tmp_path, kvm=False)
    assert res.returncode == 0 and not (folder / "docker-compose.override.yml").exists()


def test_a_second_run_keeps_the_token(tmp_path):
    install(tmp_path)
    res, folder, calls = install(tmp_path, token="")              # no token given: the script must not ask
    assert res.returncode == 0, res.stderr
    assert f"ACCESS_TOKEN={TOKEN}" in (folder / ".env").read_text().splitlines()


def test_a_wrong_token_changes_nothing(tmp_path):
    res, folder, calls = install(tmp_path, token="not a token; rm -rf")
    assert res.returncode == 1 and "not a GitHub token" in res.stderr
    assert "ACCESS_TOKEN=" in (folder / ".env").read_text().splitlines()
    assert not any("up" in c for c in calls)


def test_no_docker_stops_with_a_clear_line(tmp_path):
    res, folder, _ = install(tmp_path, docker=False)
    assert res.returncode == 1 and "Docker is not installed" in res.stderr
    assert not folder.exists()
