# The fleet worker on polopc

This kit makes polopc a worker of the fleet. The worker is a GitHub Actions self-hosted runner in a Docker
container. A workflow job with `runs-on: [self-hosted, polopc]` runs on polopc, with a real Chromium browser.

The runner is ephemeral: it takes one job, then it stops. Docker starts the container again, and the runner
registers again. Watchtower pulls a new image of the worker when the workflow `worker-image` pushes one.

You keep the keys. The token stays in `.env` on polopc. No agent gets a shell on polopc or access to your files.

## Set up the worker (one time)

1. Make the token.
   1. Open this link. It fills in the form:
      <https://github.com/settings/personal-access-tokens/new?name=polopc+worker&description=Registers+the+fleet+worker+on+polopc&target_name=lars-his-projects&expires_in=366&organization_self_hosted_runners=write>
   2. Make sure that "Resource owner" is `lars-his-projects`.
   3. Make sure that the only permission is "Organization permissions" > "Self-hosted runners": "Read and write".
      Give no repository access.
   4. Click "Generate token" and copy the token. You must be an owner of the organization: the API asks for
      admin access to the organization.

2. Set the settings of the organization. Only an organization owner can do this.
   1. Let the default runner group serve public repositories. Open
      <https://github.com/organizations/lars-his-projects/settings/actions/runner-groups>, click "Default", and
      select the option that allows public repositories. By default, only private repositories can use a runner
      group.
   2. Require approval for each workflow of a fork pull request. Open
      <https://github.com/organizations/lars-his-projects/settings/actions>. Under "Approval for running fork pull
      request workflows from contributors", select "Require approval for all external contributors". Click "Save".
   3. Note: on the GitHub Free plan, an organization has only the default runner group. GitHub documents more
      runner groups for the GitHub Team plan. A limit of a runner group to selected workflows also needs such a
      group, so this kit does not use it.

3. Make the image public, one time. GitHub makes a new package private. Open
   <https://github.com/orgs/lars-his-projects/packages/container/fleet-worker/settings>, and under "Danger Zone"
   change the visibility to "Public". The image has no secret: it is built from this public repository.

4. Install the worker on polopc with one command. It asks for the token of step 1.

   ```bash
   bash <(curl -fsSL https://raw.githubusercontent.com/lars-his-projects/fleet/main/deploy/worker/install.sh)
   ```

   The script makes the folder `~/fleet-worker`, gets `docker-compose.yml` and `.env`, writes the token into
   `.env` (only you can read that file), and starts the stack. When polopc has the device `/dev/kvm`, the script
   gives it to the worker in `docker-compose.override.yml`: a phone emulator needs it. Run the same command again
   at any time: it keeps the token and gets the newest `docker-compose.yml`.

5. Check the worker.
   1. Read the log: `docker compose logs worker`. A good log ends with "Listening for Jobs".
   2. Open <https://github.com/organizations/lars-his-projects/settings/actions/runners>. The runner `polopc` is
      "Idle".
   3. Start the workflow `worker-check`:
      <https://github.com/lars-his-projects/fleet/actions/workflows/worker-check.yml>, "Run workflow". The job
      prints the versions and "title: Example Domain".

6. Stop or remove the worker.
   - Stop: `cd ~/fleet-worker && docker compose down`. The runner goes offline. GitHub removes an ephemeral
     runner from the list when it is offline for more than 1 day.
   - Remove: `docker compose down --volumes --rmi all`, then `rm -rf ~/fleet-worker`. Revoke the token on
     <https://github.com/settings/personal-access-tokens>.

## What the worker can and cannot reach

- It cannot read your files: it has no host folder. It has two Docker volumes: `profiles` for the browser
  profiles of the agents, and `tools` for heavy tools that a job installs one time (the Android SDK and the image
  of a phone).
- It can use the device `/dev/kvm` when polopc has it, for a phone emulator. This device starts virtual machines
  inside the container; it gives no access to your files.
- It cannot control Docker: it has no Docker socket. Only the watchtower container has the socket.
- It has no root: all capabilities are dropped, `no-new-privileges` is on, and the image removes sudo.
- It has limits: 16 GB of memory, 8 CPUs, 4096 processes.
- It cannot use the GPU. The kit gives it no GPU.
- It can reach the internet and your home network, as each program on polopc can.
- An idea for more safety: a firewall rule on polopc that blocks the Docker network of the worker from the
  private address ranges (for example `192.168.0.0/16`) stops the access to the home network.

## Risks

- **Fork pull requests.** The repositories of `lars-his-projects` are public. Each person can fork a repository
  and open a pull request. The workflow file of a pull request comes from the fork, so a fork can write
  `runs-on: [self-hosted, polopc]` and run its own code on polopc. Two settings stop this:
  "Require approval for all external contributors" (step 2.2) and your review: never approve a workflow run of a
  fork pull request that you have not read. GitHub warns that approval does not make a self-hosted runner safe.
- **`pull_request_target` and other events.** A workflow with `pull_request_target` runs with no approval. No
  workflow with the label `polopc` may use `pull_request` or `pull_request_target`
  (`tests/test_fleet_worker_kit.py` checks this). Also do not give a polopc job an event that a stranger can
  start, for example `issue_comment`, if the job runs code of a pull request.
- **One job can affect the next job.** Docker restarts the same container, so the file system stays. The start
  script removes the work directory and the old runner files, but a bad job can change other files in the home
  directory or in the `profiles` volume. To start clean, run `docker compose up -d --force-recreate worker`.
- **The token.** The token can register and remove runners of the organization. The start script removes it
  from the environment before a job starts. It stays in `.env` and in `docker inspect` on polopc.
- **The image comes from `main`.** An agent can change `deploy/worker/` in a merged pull request. Watchtower
  then runs the new image within minutes. The image cannot add a host folder, the Docker socket or a privilege:
  only `docker-compose.yml` on polopc decides that, and you keep that file.
- **An update stops a running job.** Watchtower stops the worker for a new image, also during a job.
