"""The generic files of the hub must survive the bootstrap of a new project (`framework/tools/bootstrap.py`). The
bootstrap changes the name of this repository into the name of the new project. So a generic file must not use that
name for the hub or for all projects: "the registry of the hub", not the file name of the registry."""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "framework", "tools"))

import bootstrap  # noqa: E402

NAME = bootstrap.CONFIG["repo"].split("/")[1]
CONCEPT = re.compile(rf"\b(?:of the|the|a) {re.escape(NAME)}\b|\b{re.escape(NAME)}\.toml\b|\bhub \(`[^`]*/{re.escape(NAME)}`\)")


def texts():
    for path in bootstrap.generic(open(os.path.join(ROOT, "framework", "files.txt")).read()):
        try:
            yield path, open(os.path.join(ROOT, path), encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
    for path, text in bootstrap.STUBS.items():
        yield f"framework/template/{path}", text


def test_no_generic_file_uses_the_name_of_this_repository_for_the_hub():
    found = [f"{path}: {m.group(0)!r}" for path, text in texts() for m in CONCEPT.finditer(text)]
    assert found == []


def test_the_owner_of_a_new_project_is_a_login_and_not_the_first_part_of_its_repository(tmp_path):
    bootstrap.bootstrap(str(tmp_path / "a"), "some-org/new-thing")
    text = (tmp_path / "a" / "agent.toml").read_text()
    assert f'owner = "{bootstrap.CONFIG["owner"]}"' in text and 'repo = "some-org/new-thing"' in text
    bootstrap.bootstrap(str(tmp_path / "b"), "some-org/new-thing", owner="zoe")
    assert 'owner = "zoe"' in (tmp_path / "b" / "agent.toml").read_text()


def test_the_new_tests_of_the_tools_are_on_the_list_of_generic_files():
    listed = set(bootstrap.generic(open(os.path.join(ROOT, "framework", "files.txt")).read()))
    tests = {f"framework/tests/{n}" for n in os.listdir(os.path.join(ROOT, "framework", "tests")) if n.startswith("test_")}
    assert {"framework/tests/test_pacer_starter.py", "framework/tests/test_usage_share.py",
            "framework/tests/test_claim_prune_empty.py"} <= listed & tests
