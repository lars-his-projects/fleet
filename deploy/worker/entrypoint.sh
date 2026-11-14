#!/usr/bin/env bash
# Start one ephemeral runner of the organization ORG. The runner takes one job and stops.
# Then compose starts the container again, and this script registers a new runner.
set -euo pipefail

fail() { echo "worker: $*" >&2; exit 1; }

for name in ACCESS_TOKEN ORG RUNNER_NAME LABELS; do
  [[ -n "${!name:-}" ]] || fail "the variable $name is not set. Put it in .env."
done

# Get a registration token (valid for one hour). Curl reads the header from stdin, so the
# access token is not in the process list.
body="$(mktemp)"
status="$(printf 'header = "Authorization: Bearer %s"\n' "$ACCESS_TOKEN" \
  | curl -sS -K - -X POST -o "$body" -w '%{http_code}' \
      -H "Accept: application/vnd.github+json" \
      "https://api.github.com/orgs/${ORG}/actions/runners/registration-token")" \
  || fail "the request for a registration token failed (no connection to api.github.com)."
[[ "$status" == "201" ]] \
  || fail "GitHub refused the registration token: HTTP $status. Check the permission and the expiry of ACCESS_TOKEN."
reg_token="$(jq -r '.token // empty' "$body")"
rm -f "$body"
[[ -n "$reg_token" ]] || fail "the answer of GitHub has no registration token."

# A job must not see the access token: remove it before the runner starts.
unset ACCESS_TOKEN

# Remove the files of the last runner and job. Compose keeps the container file system on a restart.
cd "$HOME"
rm -rf _work .runner .credentials .credentials_rsaparams

# --disableupdate: a new runner version comes with a new image (the weekly build), not in the middle of a job.
./config.sh --unattended --ephemeral --replace --disableupdate \
  --url "https://github.com/${ORG}" --token "$reg_token" \
  --name "$RUNNER_NAME" --labels "$LABELS" --work _work
unset reg_token

exec ./run.sh
