"""The worker has the GitHub CLI (#32): the image installs it, the run gives it the token of the job."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / ".github/workflows/worker-run.yml"
CHECK = ROOT / ".github/workflows/worker-check.yml"
DOCKERFILE = ROOT / "deploy/worker/Dockerfile"


def test_the_image_installs_gh_as_root():
    text = DOCKERFILE.read_text()
    assert "install -y --no-install-recommends gh" in text
    assert text.index("install -y --no-install-recommends gh") < text.index("\nUSER runner")


def test_the_image_pipes_no_script_into_a_shell():
    for line in DOCKERFILE.read_text().splitlines():
        assert not ("curl" in line and "| sh" in line or "| bash" in line), line


def test_the_run_gives_gh_the_token_of_the_job():
    assert "GH_TOKEN: ${{ github.token }}" in RUN.read_text()


def test_the_check_prints_the_gh_version():
    assert "gh --version" in CHECK.read_text()
