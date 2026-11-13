# Decisions: the fleet

The log of the owner's decisions about the hub and about all projects together: one line per decision, the newest at
the end. `standards/PRINCIPLES.md` generalizes them. Runs only add lines here.

Columns: date · ticket · decision · recommendation (`taken`, `changed`: the owner combined or changed it, `other`:
the owner chose another option, `agent`: an agent decided and logged it, `-`: no recommendation) · principle
(`S<n>`, or `new` when no principle predicts it).

- 2026-11-13 · session · A hub above the projects: the project list, the standards, one pacer, one inbox, one dashboard, the feedback relay and the one source of the agent system. The owner took the plan as "fine for now" · taken · S1
- 2026-11-13 · session · The quota is a limit too: the owner had no usage for a day, and holds answers back to save usage. The pacer must do this brake, not the owner · other · S4
- 2026-11-13 · session · No agent gets access to the server. A preview operator sets up the previews from GitHub, with automatic updates and secrets. The owner sets up a live site by hand, with a kit: a compose file, an `.env` example, a script · other · new (S10)
- 2026-11-13 · session · A GitHub home apart from the owner's personal account. D1: the organization `lars-his-projects` for the hub and the projects, and the account `larsderpolo` for the agents · taken · S10
- 2026-11-13 · session · Many more projects will come. Each must be set up with no configuration by the owner. The owner needs one interface to start a project; the agent chose the form "New project", with a skill as its dialogue · - · new (S8)
- 2026-11-13 · session · The owner expected more and larger ideas than the first plan had. They must come in the future: roadmap goal 6 and the lab scout · - · S6
- 2026-11-13 · session · D2: the stages and weights at the start: aoe2mc polish 2, travel-aggregator polish 2, tumach-dance polish 1, then maintain after the go-live · taken · S4
- 2026-11-13 · session · D3: an even weekly pace with a reserve of 10 % for the owner's own sessions. It replaces the pacing decisions of 2026-10-27, 2026-11-04 and 2026-11-09 when the one pacer exists · taken · S4
- 2026-11-13 · session · D4: polopc is a worker and is on all day. The pacer checks that it is online and includes the tickets for it only then · changed · S9
- 2026-11-13 · session · D4: an agent can use real travel sites in a browser profile of its own; Jeroen agrees. This changes P1 of travel-aggregator · taken · S2
- 2026-11-13 · session · D5: "decide and log" for decisions that are easy to undo, with a weekly digest and a veto · taken · S2
- 2026-11-13 · session · D6: the attention budget is 30 minutes per week · taken · S2
- 2026-11-13 · session · D7: the previews run on a VM of their own; the live sites stay on other machines · taken · S10
- 2026-11-13 · session · Phase 0 of the hub goes to `main` with the recommendations D1 to D7 · taken · S1
- 2026-11-13 · session · The hub is public, and the fleet page is at https://lars-his-projects.github.io/fleet/ · taken · S4
- 2026-11-13 · session · "move": each project uses its new name in the organization (one PR per project) · taken · S5
- 2026-11-13 · session · "guard": a weekly pace from the start of the week in each project (`week_guard = true`, `week_free = 0`), until the one pacer exists · taken · S4
- 2026-11-13 · session · "share": each project plans with its part of the weekly budget (`week_share`, its weight in `fleet.toml`) and the runs leave the reserve of D3 (`week_reserve`) to the owner until 12 hours before the reset; before, each of four pacers planned with the whole budget of the account · taken · S4
- 2026-11-13 · card 6 · How a new project gets its runs with no step of the owner: A, one set of scheduled tasks with no repository and one set of organization secrets for the whole fleet, with a test first (B: the worker on polopc does the clicks; C: a step card for each project) · A (owner) · S8
- 2026-11-13 · session · A card names its person with the GitHub assignee, not with a label `for-<name>`: GitHub shows each person one list of all cards · taken (owner) · S2
- 2026-11-13 · card 6 · The test of option A failed: a run with no repository has no tool to attach one. A session can start a run directly in a repository. The changed proposal "A2" (one starter session for the fleet) waits for the owner · open · S8
