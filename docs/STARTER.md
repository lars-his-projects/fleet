# The starter session of the fleet

Decision A2 of card 6 (owner, 2026-11-13). The goal is principle S8: a new project needs no setup from the owner.
Before, each project needed three scheduled tasks, three API tokens and seven secrets that only the owner can make.

## Status on 2026-11-13: not in use

The parts were tested on 2026-11-13. The starter needs a permission that only the owner can give (card 6).

| Part | Result |
|---|---|
| A session with a person starts a run in a repository (the repository, the model and the prompt) | Works |
| A session with no repository has the tool for that, and it can read the public hub | Works |
| A timer sends a tick to the starter session at a scheduled time | Works. A start of the timer by hand makes a new session with no tools: do not use it |
| The starter downloads the hub and runs `python3 -m hub.starts` | Refused by the permission check of the platform ("Unauthorized Access") |
| The starter reads the registry and the pacer records as data, with no code from a repository | Works |
| The starter session, with no person, starts a run | Refused by the permission check: the owner must allow the tool in the settings, or confirm each call |

Until the owner gives that permission, no project depends on the starter. The hub starts its runs with its scheduled
tasks. A project with `starts = "session"` (street-quiz) plans its runs and starts none.

The text below is the design. The second form of the starter read only data (the registry and the newest pacer
record of each project) and used the same rules as `hub/starts.py`.

## How a run starts

1. The pacer workflow of a project (`pacer.yml`, `framework/tools/pacer.py`) reads the quota each 10 minutes and plans
   the runs: `k` runs, with the lane runs in `plan`. It writes the plan to the branch `metrics` of the project.
2. With `starts = "session"` in `[pacing]` of `steering/system/system.toml`, the workflow sends no call. Its record
   says `"starts": "session"`.
3. The starter is a session with no repository and a cheap model. A timer starts one tick each hour. In a tick the
   starter clones this repository, runs `python3 -m hub.starts`, and starts one run for each item of the list:
   a new session in the repository of the project, with the prompt of the lane.
4. The run is a usual run: it has one repository, its skills and its rules. It cannot start a run: the settings of
   each project deny the session tools.

## The guards

- The plan comes from the pacer workflow, not from a model. The starter starts only what `hub/starts.py` prints.
- Only a project of `fleet.toml` whose newest record says `"starts": "session"` gets a start.
- A plan older than 20 minutes starts nothing.
- At most 4 starts for one project and 8 starts in one tick (`LIMIT_PROJECT`, `LIMIT_TICK`).
- A run stops at its start when the quota target is 0 (the `scheduled` skill).

## What is not in this repository

- The model and the effort of each lane. They are in the prompt of the timer of the starter, as they were in the
  scheduled tasks before. The lanes: `main`, `haiku`, `deep`.
- The starter session and its timer. A session of the owner makes them (`mcp__claude-code-remote`: one session with
  no repository, one scheduled task that sends the tick to that session each hour).

## Known limits

- A run can start up to one hour after its plan. Before, the limit was 10 minutes.
- A run shows in the session list of the owner, not in the list of scheduled tasks. The starter archives a finished
  run after 2 hours. A run sends no phone notification.
- The starter reads the branch `metrics` with no login: it serves only public repositories.
- A run can write to the branch `metrics` of its project. A wrong record can thus ask for runs. The limits above
  hold, and each run checks the quota target at its start.

## Check and stop

- Check: `python3 -m hub.starts` prints the list for this moment and the reason for each project with no start.
- Stop the starts of one project: remove the line `starts = "session"`, or add `paused` to its status issue.
- Stop the starter: disable the scheduled task "fleet starter" at https://claude.ai/code/routines.
