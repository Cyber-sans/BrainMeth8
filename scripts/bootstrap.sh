#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

# shellcheck disable=SC1091
source .env

mkdir -p secrets
if [[ ! -s secrets/rcon_password.txt ]]; then
  umask 077
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32 > secrets/rcon_password.txt
  else
    tr -dc 'A-Za-z0-9' </dev/urandom | head -c 48 > secrets/rcon_password.txt
    printf '\n' >> secrets/rcon_password.txt
  fi
  echo "Generated secrets/rcon_password.txt"
fi

sudo install -d -m 775 -o "$USER" -g "$(id -gn)" "${PROD_DATA_DIR:-/srv/minecraft/brainmeth/prod}" "${TEST_DATA_DIR:-/srv/minecraft/brainmeth/test}" "${BACKUP_DIR:-/srv/minecraft/brainmeth/backups}"

./scripts/validate.sh

echo
echo "Bootstrap complete."
echo "Start test: docker compose --profile test up -d"
echo "Start prod: docker compose --profile prod up -d"
