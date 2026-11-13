# Environment

The project part of the cloud environment of street-quiz (`framework/docs/STEERING.md`).

## Network

"Allow package managers" gives npm and PyPI. `scripts/allowed-domains.txt` adds:

- `github.com`: git.
- `nodejs.org`: Node 24 for the setup script, when the image has an older Node.

No map host and no data host is on the list on purpose: the tests use stored data, never a live map or data service
(P3). An agent that needs another host adds it to the file and opens a `needs-human` ticket for the owner.

## Setup script

`scripts/cloud-setup.sh` installs the Python tools (pytest, ruff, numpy) and Node 24 when the image has an older Node.
It does not read the repository. The SessionStart hook (`.claude/hooks/session-start.sh`) installs
`requirements-dev.txt` and runs `npm ci`.

## Resources of the owner

What the owner has for the project: the computer, the devices, the accounts and licenses, the budget and the Claude
plan (the owner gave it when the project started). Do not plan work that needs a resource that is not here: make a decision
ticket for it.

- **Devices:** a phone and a computer. The owner opens the live preview on the phone.
- **Worker:** a computer "polopc" (Debian, Chrome) can come later as a worker.
- **Accounts:** no paid service.
- **Budget:** free only. Each cost gets a decision ticket.
- **Claude plan:** three lanes: the main task, a haiku lane and a deep lane.
