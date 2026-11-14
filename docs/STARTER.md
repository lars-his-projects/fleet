# The starter session of the fleet

Decisions A2 and P of card 6 (owner, 2026-11-13 and 2026-11-14). The goal is principle S8: a new project needs no
setup from the owner. Before, each project needed three scheduled tasks, three API tokens and seven secrets that only
the owner can make.

## Status on 2026-11-14: in use for each project

- The starter is the repository `lars-his-projects/fleet-starter`, one session with only that repository, and the
  scheduled task "fleet starter" that sends the session one tick each hour.
- street-quiz was the first project that the starter served. Proved there on 2026-11-14: the starter started runs
  with no person, and those runs did tickets and merged five pull requests.
- Since 2026-11-14 the starter serves each project of the fleet: aoe2mc, travel-aggregator, tumach-dance and the hub
  have `starts = "session"` too. Their scheduled tasks stay in the account, but no pacer calls them.
- The lanes have the names of their models (owner, 2026-11-14): `haiku`, `sonnet`, `opus` and `fable`. The starter
  starts each run with the model of its lane, so a new lane costs the owner nothing.

## How a run starts

1. The pacer workflow of a project (`pacer.yml`, `framework/tools/pacer.py`) reads the quota each 10 minutes and plans
   the runs: `k` runs, with the lane runs in `plan`. It writes the plan to the branch `metrics` of the project.
2. With `starts = "session"` in `[pacing]` of `steering/system/system.toml`, the workflow sends no call. Its record
   says `"starts": "session"`.
3. On a tick the starter session runs `python3 plan.py` of its own repository. The script reads the registry of the
   hub (`fleet.toml`) and the newest pacer record of each project, as data. It prints the list of runs to start.
4. The starter starts one run for each item: a new session in the repository of the project, with the fixed start
   text of the lane: `/scheduled max` for the default lane `opus`, and `/scheduled max lane NAME` for the lanes
   `haiku`, `sonnet` and `fable`.
5. The run is a usual run: it has one repository, its skills and its rules. It cannot start a run: the settings of
   each project deny the session tools.

## The permission

The platform refuses a start by a session with no person. It also refuses a script that such a session downloaded.
The tests of 2026-11-13 showed both. So the owner gave the starter a permission (card 6, option P):

- `.claude/settings.json` of `fleet-starter` allows three session tools: start a session, list its sessions, and
  archive a finished session. It also allows the command of `plan.py`. It denies the other session tools and each
  change of a file.
- The rule holds only for a session with that one repository. No project and no run of a project has it.
- Only the owner decides a change of that `allow` list.

## The guards

- The plan comes from the pacer workflow, not from a model. The starter starts only what `plan.py` prints.
- Only a repository of the organization that is in `fleet.toml`, and only when its newest record says
  `"starts": "session"`: the starter never starts a run in a project that starts its runs itself.
- A plan older than 20 minutes starts nothing.
- At most 4 starts for one project and 8 starts in one tick. The tests of `fleet-starter` guard these limits.
- The start text is fixed for each lane. No text of a project goes into a start.
- A run stops at its start when the quota target is 0 (the `scheduled` skill).

## What is not in a repository

- The model of each lane. It is in the text of the tick, as the model was in each scheduled task before:
  `haiku = claude-haiku-5-5, sonnet = claude-sonnet-5-5, opus = claude-opus-5-5, fable = claude-fable-5-2`.
- The starter session and its timer. A session of the owner made them with the session tools.

## Known limits

- With the permission, the platform does not let the starter select the effort of a run, and a line `effortLevel`
  in the settings of a project did not change it: the owner saw the effort medium in each run of street-quiz
  (2026-11-14). So the lanes differ by their model only.
- A run can start up to one hour after its plan. With the scheduled tasks, the limit is 10 minutes.
- A run shows in the session list of the owner, not in the list of scheduled tasks. The starter archives a finished
  run after 2 hours. A run sends no phone notification.
- The starter reads the branch `metrics` with no login: it serves only public repositories.
- A run can write to the branch `metrics` of its project. A wrong record can thus ask for runs of that project. The
  limits above hold, and each run checks the quota target at its start.
- The starter session lives long, so each tick reads a longer history. A new starter session each week keeps a tick cheap.
- Do not start the timer by hand: that makes a new session with no repository and no permission. The timer works at
  its scheduled times only.

## Add a project to the starter

1. The project has `starts = "session"` in `[pacing]` of its `steering/system/system.toml` (the template has it),
   and the lanes of the template in `[pacing]`.
2. The project is in `fleet.toml` with a stage that has quota.
3. Its pacer workflow runs. Its repository is public.

## Check and stop

- Check: `python3 plan.py` in `fleet-starter` prints the list for this moment and the reason for each project with no
  start. `python3 -m hub.starts` in this repository gives the same list from the same rules.
- Stop the starts of one project: remove the line `starts = "session"`, or add `paused` to its status issue.
- Stop the starter: disable the scheduled task "fleet starter" at https://claude.ai/code/routines.
- Remove the permission: remove the three session tools from the `allow` list of `fleet-starter`.
