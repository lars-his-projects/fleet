# Learnings

The agent writes here what it learned the hard way. Each line must save time in a later session.

## Environment and libraries
- A hub session can write only to the hub. Read a project with `gh api -X GET search/issues` or `search/code`
  (`repo:lars-his-projects/<name>`). A hub ticket that needs a change in a project waits for a ticket of that project.

## Code
- A change of text in a generic file (`framework/`, `.claude/`): run `tests/test_fleet_bootstrap_words.py` before the
  push. It fails on "the fleet" and "of the fleet": write "the hub" or "all projects".
