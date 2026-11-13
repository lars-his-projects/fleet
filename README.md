# fleet

The hub of the AI-first projects of Larspolo. Agents (Claude Code) build the projects. The owner gives direction only:
the roadmap, new projects, approvals, and feedback. The hub is the one place for the project list, the rules that all
projects share, and the overview.

## What is here

| Part | What it is |
|---|---|
| `fleet.toml` | The registry: each project with its stage, its weight (its share of the quota), its owners and its addresses |
| `standards/` | The rules for all projects: the principles (S1 to S10), when an agent asks a person, design, resources |
| `dashboard/` | The fleet page: one dashboard for all projects, built by a workflow with no Claude quota |
| `steering/project/ROADMAP.md` | The plan of the hub: what works (`[x]`) and what comes next |
| `steering/project/DECISIONS.md` | The log of the owner's decisions about the fleet |
| The form "New project" | The one door for a new project (Issues → New issue) |

## Steer

| You want to | Do this |
|---|---|
| See all projects | Open the fleet page |
| See what waits for you | The section "Inbox" of the fleet page: each open `needs-human` ticket of each project |
| Start a project | Issues → New issue → **New project**. Write the idea in some sentences. |
| Give a project more or less of the quota | Change `stage` or `weight` of the project in `fleet.toml` |
| Change a rule for all projects | Edit a file in `standards/` |
| Change the plan of the hub | Add or change a line in `steering/project/ROADMAP.md` |

Until the roadmap feature `projects:auto` works, a session sets a new project up: start a Claude Code session with
this repository and write "set up the new project of issue N".

## The fleet page

The page is at **https://lars-his-projects.github.io/fleet/**.

The workflow **Fleet page** builds `index.html` and `data.json` from the `metrics` branch, the roadmap and the open
issues of each project in `fleet.toml`. It runs on a timer twice per hour, on each change of the page code or of
`fleet.toml`, and by hand (Actions → Fleet page → Run workflow).

The hub is public, and it holds no secret. If the repository becomes private:

- GitHub Pages stops on the free plan. Each run of the workflow then keeps the page as the artifact `github-pages`
  (Actions → the run → Artifacts).
- The timer stops, because a private repository pays for its Actions minutes. A push and a start by hand still build.
- To publish again: make the repository public, set Settings → Pages → Source to **GitHub Actions**, and start the
  workflow one time.

## Commands

```bash
python3 -m pip install -r requirements-dev.txt
```

```bash
ruff check . && python3 -m pytest
```

```bash
python3 -m hub.registry
```

```bash
python3 -m dashboard.build --out _site
```

The last command reads GitHub. For a build with no network, see the top of `dashboard/build.py`.

## What comes next

The roadmap has six goals. The sequence: one pacer for the account with an even weekly pace and a reserve for the
owner, and the agent system as one source for all projects; then polopc as a worker, the preview operator and the
live kits; then feedback in each product; then the lab that tests each larger idea and each new model.
