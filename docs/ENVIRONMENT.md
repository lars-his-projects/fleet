# Environment

The project part of the cloud environment of fleet (`framework/docs/STEERING.md`).

## Network

The tests need no host outside the package managers: each test makes its own data.
The page build with no `--offline` reads `github.com` (the `metrics` branches) and `api.github.com` (the roadmaps and
the issues). The workflow `fleet-page.yml` does that build. A run builds with `--offline`.

## Setup script

`scripts/cloud-setup.sh` installs nothing: Python and git are in the image, and the SessionStart hook installs the
packages of `requirements-dev.txt`. The hub can use the cloud environment of the other projects.

## Resources of the owner

What the owner has for the project: the computer, the devices, the accounts and licenses, the budget and the Claude
plan (the `new-project` skill writes it). Do not plan work that needs a resource that is not here: make a decision
ticket for it.

- The resources of all projects are in `standards/RESOURCES.md`: the Claude subscription, the GitHub organization,
  the owner's computer polopc, the home server and its configuration repository, the addresses and the services.
