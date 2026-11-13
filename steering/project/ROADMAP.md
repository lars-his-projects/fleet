# Roadmap of the fleet

The hub exists so that the owner gives direction only: the roadmap, new projects, approvals, and feedback while the
owner uses a product. The owner took this plan on 2026-11-13 as "fine for now" (`DECISIONS.md`), and expects larger
ideas: goal 6 and the lines with "(larger idea)". The data and the reasons of the plan are in the fleet briefing, a
private page of the owner: https://claude.ai/artifact/QoJzJKjajYSwAikWqBFEwa

A feature line is ``- [ ] `goal:feature` text``. The lines below it are its sub-items. `[x]` means: it works on `main`.
The sequence of the work is the sequence of the phases: 1 the pacer and the sync, 2 the workers and the setup,
3 the feedback, 4 the lab.

## 1. One overview

- [x] `overview:registry` `fleet.toml` lists each project with its stage, its weight, its owners and its addresses
  - A fault in the file stops CI with one clear line (`hub/registry.py`)
- [x] `overview:page` One fleet page for all projects, built by a workflow with no Claude quota
  - Now: the runs at work, the ready tickets, the last run report and the pacer of each project
  - Inbox: each open `needs-human` ticket of each project
  - Progress: the roadmap features of each project and goal
  - Usage: the weekly curve against an even pace, and the split between the projects
  - Cost points: the usage of each lane, per PR, and in reports with no PR
- [x] `overview:publish` The page has a fixed address that the owner opens on a phone
  - https://lars-his-projects.github.io/fleet/ (the hub is public since 2026-11-13; a timer builds the page twice per hour)
- [ ] `overview:live` The page builds in each pacer cycle and shows each run at work with its lane and its ticket
- [ ] `overview:value` The page shows value and not only PRs: accepted features per point of quota, rework,
  features that were removed later, and the usage with no PR by kind (refill, check, review, repair, no ticket)
- [ ] `overview:week` "New this week" for each project in plain words, with a link to the preview
- [ ] `overview:system` A system section: the experiments, the version of the agent system in each project, the end
  date of each token, the state of each worker
- [ ] `overview:money` The real money per month: the subscription, the domains, the services

## 2. One pacer and one budget

- [ ] `pacer:one` One pacer for the account starts the runs of all projects
  - Today each project has its own pacer, and the three pacers read the same quota
  - An even pace to 100 % at the weekly reset; the 5-hour window is a guard only
  - `week_reserve` of the week stays free for the owner's sessions; the pacer releases it in the last hours
  - The weights of `fleet.toml` split the budget; a project with no ready work gives its share to the next project
  - Each week the page shows the usage at the reset and the cause of each unused point
- [ ] `pacer:ladder` The work ladder: when a step is empty, the quota goes one step down
  - 1 feedback and bugs; 2 approved roadmap features; 3 checks that a machine can do with a real device;
    4 quality work with evidence; 5 experiments of the lab; 6 prototypes of a proposed direction on a preview branch
  - A prototype does not merge to `main` before the owner approves the direction
- [ ] `pacer:lanes` A lane router: each kind of ticket goes to the cheapest lane whose rework stays below a limit
  - A limit for the share of the deep lane (52 % of the usage on 2026-11-13)
- [ ] `pacer:value` (larger idea) The next point of quota goes to the work with the best measured value
  - While the owner gives feedback, those tickets get a fast lane: the fix is on the preview before the owner stops

## 3. One agent system

- [x] `system:standards` One merged copy of the standards: principles, the human gate, design, resources
- [ ] `system:move` The projects use their new home in the organization
  - `repo` in `agent.toml`, the image names (`ghcr.io/larspolo/...`), the Pages addresses, the links in the documents:
    the PRs aoe2mc 6450, travel-aggregator 2864 and tumach-dance 863 of 2026-11-13
  - The servers pull the new image names (the owner steps are in those PRs)
  - The scheduled tasks point at the new repositories
- [ ] `system:source` The agent system (`framework/`) lives in the hub
  - Each project pins a version; a sync workflow brings a fix from the hub to each project
  - The three copies of the system principles are replaced by `standards/`
- [ ] `system:owners` Instructions come only from owner logins, and the agents act as the login `agent` of `fleet.toml`
  - A check that no tool treats a text of the agent login as an instruction

## 4. Little owner work

- [ ] `human:cards` The card formats of `standards/HUMAN.md` in each project
  - A lint refuses a card with no minutes, no default, or no reason why a machine cannot do it
- [ ] `human:batch` One card for one request, and a weekly digest of the "decide and log" decisions with a veto
- [ ] `human:one-tap` A thumbs-up of an owner login on a card means "take the recommendation"
- [ ] `human:budget` The attention budget: minutes on each card; the inbox sorts by value for each minute
- [ ] `human:trust` The rate of taken recommendations for each kind of decision moves a kind between "ask first" and
  "decide and log"
- [x] `projects:form` The form "New project" in the hub: the idea, the users, the first good result, limits
- [ ] `projects:auto` A new project needs no other step of the owner
  - A workflow makes the repository from the template, adds it to `fleet.toml`, and sets the labels, the rules and Pages
  - A run writes the roadmap; the owner gets one card: approve or change the roadmap
  - The skill `/new-project` fills the same form with a dialogue
- [ ] `projects:house-stack` A template with a login, a preview, the feedback button, usage counts and a deploy kit
  that work on the first day, and one design system for the fleet with a theme for each project
- [ ] `workers:polopc` polopc is a worker: a user `agent`, containers, a worker service that asks for work
  - The environment of a project is a container file in git; an agent changes it by a PR
  - One bootstrap command for the owner
- [ ] `workers:devices` A ticket that needs a device has a label; the worker sends a heartbeat; the pacer includes
  such a ticket only while a worker with the device is online
- [ ] `workers:real-sites` An agent uses real travel sites in a browser profile of its own on polopc
  - A decision line and the new text of P1 in travel-aggregator
- [ ] `setup:preview-operator` One compose stack that the owner starts one time on the server
  - It reads `fleet.toml` and the folder `deploy/preview/` of each project from GitHub, with outbound connections only
  - It applies a new image and a changed compose file, and it publishes the state of each preview
  - It refuses privileged containers, host folders and the Docker socket; the previews have a VM of their own
- [ ] `setup:secrets` A file in the repository says what each variable is; the operator makes the values on the server
  - A key that only the owner has goes one time into a shared store on the server, for all projects
- [ ] `setup:live-kit` Each project has `deploy/live/`: a compose file, an `.env` example with one comment per
  variable, and a setup script; CI tests the kit with false values
- [ ] `design:systems` Each project has one design system that the owner approved one time, and the machine checks
  of `standards/DESIGN.md`

## 5. Feedback in the product

- [ ] `feedback:relay` One relay receives all feedback and makes an issue with the label `feedback` in the correct
  repository; the context goes to a private store, not into a public issue
- [ ] `feedback:web` A feedback button in the web apps: the element, the text, the last steps as a recording, the
  console errors, a screenshot; the values of input fields stay hidden
- [ ] `feedback:userscript` The same button in the userscript panel of travel-aggregator
- [ ] `feedback:minecraft` Two Minecraft servers that are always on (`latest` and `release`) and a chat command that
  sends the text with the position, the target, the selection, the game tick and a copy of the world
- [ ] `feedback:loop` A feedback issue is P1: a run in the next cycle plays the recording again, writes a failing
  test, makes the ticket and answers what it understood; when the fix is on the preview, the product shows a note
- [ ] `feedback:hotkey` (larger idea) One key on polopc records the voice, takes a screenshot and keeps the last
  30 seconds of the screen; a speech model on the GPU writes the text; the window in focus selects the project

## 6. The system improves itself

- [ ] `lab:experiments` A part of the quota goes to tests of a champion against a challenger
  - An experiment names its hypothesis, its change, its measure, its sample in merged PRs and its stop rule
- [ ] `lab:benchmark` A benchmark of old tickets: closed tickets with their start commit and the tests of their PR;
  a new setup does them again in a sandbox; the result is a pass rate and a cost
- [ ] `lab:models` A daily check finds a new model; the lab runs the benchmark on each lane and writes the lane map
- [ ] `lab:scout` Each week one run reads the release notes of Claude Code, the new models and the numbers of the
  fleet, and writes at most three proposal cards
- [ ] `lab:synthetic-users` (larger idea) Persona agents use each product each day and send feedback through the relay
- [ ] `lab:owner-model` (larger idea) A predictor of the owner's answers, tested on the logged decisions; it answers
  the kinds of decision that it predicts well; the owner corrects it with a few samples per week
- [ ] `lab:factory` (larger idea) The expensive model writes acceptance checks that a machine can run and cuts the
  work into small tickets; the cheap model builds until the checks pass
- [ ] `lab:directions` (larger idea) Direction cards with a live prototype, from evidence: the features in use,
  groups of feedback, journeys that fail; a card can propose to remove a feature
- [ ] `lab:video` (larger idea) The week as a video: a short recording of what is new in each project, with a
  thumbs-up or a thumbs-down at a moment in the video
- [ ] `lab:capacity` (larger idea) More capacity as a proposal card: what a second account adds for its price
