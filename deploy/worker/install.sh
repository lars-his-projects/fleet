#!/usr/bin/env bash
# Install or update the fleet worker on this computer. One command for the owner:
#
#   bash <(curl -fsSL https://raw.githubusercontent.com/lars-his-projects/fleet/main/deploy/worker/install.sh)
#
# It makes the folder ~/fleet-worker, gets docker-compose.yml and .env, asks for the token one time, gives the
# worker the device /dev/kvm when this computer has it (a phone emulator needs it), and starts the stack.
# Run it again at any time: it keeps .env and the token.
set -euo pipefail

RAW="${FLEET_WORKER_RAW:-https://raw.githubusercontent.com/lars-his-projects/fleet/main/deploy/worker}"
DIR="${FLEET_WORKER_DIR:-$HOME/fleet-worker}"
KVM="${FLEET_WORKER_KVM:-/dev/kvm}"

fail() { echo "install: $*" >&2; exit 1; }

command -v docker > /dev/null || fail "Docker is not installed on this computer."
docker compose version > /dev/null 2>&1 || fail "The Compose plugin of Docker is not installed (docker compose)."

mkdir -p "$DIR"
cd "$DIR"
curl -fsSL -o docker-compose.yml "$RAW/docker-compose.yml" || fail "No download of docker-compose.yml from $RAW."
if [[ ! -f .env ]]; then
  curl -fsSL -o .env "$RAW/.env.example" || fail "No download of .env.example from $RAW."
fi
chmod 600 .env

# The token: only when .env has none. The text does not show on the screen.
if ! grep -q '^ACCESS_TOKEN=.' .env; then
  token="${FLEET_WORKER_TOKEN:-}"
  if [[ -z "$token" ]]; then
    read -rsp "Paste the token of step 1 and press Enter: " token
    echo
  fi
  [[ "$token" =~ ^[A-Za-z0-9_]+$ ]] || fail "That is not a GitHub token (letters, digits and _ only). Nothing changed."
  sed -i "s|^ACCESS_TOKEN=.*|ACCESS_TOKEN=${token}|" .env
  unset token
fi

# A phone emulator needs the device /dev/kvm. Give it to the worker only when this computer has it: the
# worker user gets the group of the device, and no other right.
if [[ -e "$KVM" ]]; then
  cat > docker-compose.override.yml <<EOF
# Made by install.sh: this computer has $KVM, so the worker can run a phone emulator.
services:
  worker:
    devices:
      - $KVM
    group_add:
      - "$(stat -c %g "$KVM")"
EOF
  echo "install: the worker gets $KVM (for a phone emulator)."
else
  rm -f docker-compose.override.yml
  echo "install: this computer has no $KVM. The worker runs with no phone emulator."
fi

docker compose pull || fail "No pull of the image. If the package is private: step 3 of the README makes it public."
docker compose up -d
echo "install: the worker runs. Check it:"
echo "  docker compose -f $DIR/docker-compose.yml logs worker     (a good log ends with: Listening for Jobs)"
echo "  https://github.com/organizations/lars-his-projects/settings/actions/runners     (the runner polopc is Idle)"
echo "  https://github.com/lars-his-projects/fleet/actions/workflows/worker-check.yml   (Run workflow)"
