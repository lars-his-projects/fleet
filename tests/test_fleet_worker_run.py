"""The workflow of one agent run on the worker (`.github/workflows/worker-run.yml`, #20): its guard and its form.

The checks read the text of each workflow that runs the Claude Code CLI on the worker. PyYAML is not a dependency.
"""
import re

import pytest
from test_fleet_worker_kit import LABEL, WORKFLOWS, triggers

RUN = WORKFLOWS / "worker-run.yml"
# Each word skips the permission checks of the CLI, or the settings of the project (its deny list and its hooks).
SKIPS = ("dangerously", "bypassPermissions", "--bare", "--safe-mode", "--restricted", "--setting-sources",
         "--disallowedTools", "--allowedTools", "--allowed-tools", "--disallowed-tools")
ALLOWED_SECRETS = {"CLAUDE_CODE_OAUTH_TOKEN"}


def code(text):
    """The text of a workflow with no comment."""
    return "\n".join(ln.split(" #")[0] for ln in text.splitlines() if not ln.lstrip().startswith("#"))


def cli_lines(text):
    """The lines of a workflow that call the CLI with a prompt, each with its continuation lines."""
    out, lines = [], code(text).splitlines()
    for i, ln in enumerate(lines):
        if re.search(r"\bclaude\s+(-p|--print)\b", ln):
            full = ln
            while full.rstrip().endswith("\\") and i + 1 < len(lines):
                i += 1
                full = full.rstrip()[:-1] + " " + lines[i].strip()
            out.append(full)
    return out


def secrets_used(text):
    return set(re.findall(r"\$\{\{\s*secrets\.([A-Za-z0-9_]+)", code(text)))


def worker_workflows():
    return [p for p in sorted(WORKFLOWS.glob("*.y*ml")) if LABEL in code(p.read_text())]


def test_the_run_workflow_calls_the_cli():
    assert cli_lines(RUN.read_text()), "worker-run.yml does not call `claude -p`"


@pytest.mark.parametrize("path", worker_workflows(), ids=lambda p: p.name)
def test_no_worker_workflow_skips_the_permission_checks(path):
    text = code(path.read_text())
    for word in SKIPS:
        assert word not in text, f"{path.name} has {word}"


@pytest.mark.parametrize("path", worker_workflows(), ids=lambda p: p.name)
def test_each_cli_call_has_a_guard_and_asks_no_person(path):
    for line in cli_lines(path.read_text()):
        mode = re.search(r"--permission-mode[ =](\S+)", line)
        assert mode and mode.group(1) in ("auto", "dontAsk", "manual"), line
        assert re.search(r"--permission-prompts[ =]none\b", line), line


@pytest.mark.parametrize("path", worker_workflows(), ids=lambda p: p.name)
def test_a_worker_workflow_has_no_other_secret(path):
    text = path.read_text()
    assert secrets_used(text) <= ALLOWED_SECRETS, secrets_used(text) - ALLOWED_SECRETS
    assert not re.search(r"secrets:\s*inherit", code(text)), f"{path.name} takes each secret of the caller"
    assert "toJSON(secrets)" not in code(text).replace(" ", "")


def test_the_run_workflow_starts_only_by_hand_or_by_a_call():
    assert triggers(RUN.read_text()) == {"workflow_dispatch", "workflow_call"}


def test_a_caller_with_another_event_gets_no_job():
    assert re.search(r"^    if: github\.event_name == 'workflow_dispatch'$", code(RUN.read_text()), flags=re.M)


def test_no_input_goes_into_a_shell_script():
    """An input in a `run:` script is code of the person who starts the run. An `env:` value is only text."""
    for ln in code(RUN.read_text()).splitlines():
        if "${{" in ln and re.search(r"\$\{\{\s*(inputs|github\.event)\.", ln):
            assert re.match(r"^\s+[A-Z][A-Z0-9_]*: \$\{\{[^}]*\}\}$", ln), ln


def test_the_job_can_start_ci_for_its_pr():
    text = code(RUN.read_text())
    for line in ("contents: write", "pull-requests: write", "issues: write", "actions: write"):
        assert re.search(rf"^  {line}\s*$", text, flags=re.M), line


@pytest.mark.parametrize("line,ok", [
    ("claude -p \"$P\" --permission-mode auto --permission-prompts none", True),
    ("claude -p \"$P\" --permission-mode auto", False),
    ("claude -p \"$P\" --permission-prompts none", False),
    ("claude --print \"$P\" --permission-mode acceptEdits --permission-prompts none", False),
])
def test_the_reader_of_the_cli_lines(line, ok):
    found = cli_lines(f"jobs:\n  a:\n    steps:\n      - run: |\n          {line}\n")
    assert len(found) == 1
    mode = re.search(r"--permission-mode[ =](\S+)", found[0])
    good = bool(mode and mode.group(1) in ("auto", "dontAsk", "manual") and re.search(r"--permission-prompts[ =]none\b", found[0]))
    assert good is ok


def test_the_reader_joins_a_continued_line():
    text = "      - run: |\n          claude -p x \\\n            --permission-mode auto \\\n            --permission-prompts none\n"
    assert "--permission-prompts none" in cli_lines(text)[0]
