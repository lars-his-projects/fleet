"""The registry: the form of `fleet.toml` and the faults that `hub/registry.py` must refuse."""
import copy

import pytest

from hub import registry

BASE = {
    "fleet": {"owner": "owner-login", "org": "an-org", "week_reserve": 0.1, "attention_minutes": 30},
    "stages": {"build": 3, "polish": 2, "paused": 0},
    "projects": {
        "first": {"repo": "an-org/first", "stage": "build"},
        "second": {"repo": "an-org/second", "stage": "polish", "weight": 1, "owners": ["a", "b"], "preview": "https://x.test"},
    },
}


def test_defaults_come_from_the_stage_and_the_fleet():
    fleet = registry.parse(BASE)
    first, second = fleet.projects
    assert (first.weight, first.owners, first.branch) == (3.0, ("owner-login",), "main")
    assert first.roadmap == "steering/project/ROADMAP.md" and first.links == {}
    assert (second.weight, second.owners, second.links) == (1.0, ("a", "b"), {"preview": "https://x.test"})


def test_projects_keep_the_order_of_the_file():
    assert [p.name for p in registry.parse(BASE).projects] == ["first", "second"]


def test_the_agent_login_is_optional():
    assert registry.parse(BASE).agent == ""
    data = copy.deepcopy(BASE)
    data["fleet"]["agent"] = "agent-login"
    assert registry.parse(data).agent == "agent-login"


@pytest.mark.parametrize("change, text", [
    (lambda d: d["projects"]["first"].update(stage="later"), "stage must be one of"),
    (lambda d: d["projects"]["first"].update(repo="no-owner"), "repo must be owner/name"),
    (lambda d: d["projects"]["first"].update(wieght=2), "unknown key 'wieght'"),
    (lambda d: d["projects"]["first"].update(weight=-1), "weight must be"),
    (lambda d: d["projects"]["first"].update(owners=[]), "owners must be"),
    (lambda d: d["fleet"].update(week_reserve=1.0), "week_reserve"),
    (lambda d: d["fleet"].update(colour="x"), "unknown key 'colour'"),
    (lambda d: d["fleet"].pop("owner"), "owner must be"),
    (lambda d: d["fleet"].update(agent=7), "agent must be"),
    (lambda d: d.pop("stages"), "at least one stage"),
])
def test_a_fault_names_the_table_and_the_key(change, text):
    data = copy.deepcopy(BASE)
    change(data)
    with pytest.raises(registry.RegistryError, match=text):
        registry.parse(data)


def test_the_file_of_the_hub_has_the_correct_form():
    registry.load()     # raises RegistryError for a fault; the content of the file is the owner's


def test_a_file_that_is_not_toml_is_a_registry_fault(tmp_path):
    bad = tmp_path / "fleet.toml"
    bad.write_text("[fleet\n")
    with pytest.raises(registry.RegistryError):
        registry.load(bad)
