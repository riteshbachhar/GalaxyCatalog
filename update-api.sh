#!/usr/bin/env bash
#
# Pull the latest code and restart the API. The database is untouched.
#
#   ./redeploy.sh

set -euo pipefail
cd "$(dirname "$0")"

HOST_PORT="${HOST_PORT:-8001}"

git pull

# shellcheck disable=SC1091
set -a; . ./.env; set +a

# Forgetting this expands the password to an empty string, and the failure
# shows up later as 'fe_sendauth: no password supplied'.
[ -n "${GALAXY_RO_PASSWORD:-}" ] || { echo "GALAXY_RO_PASSWORD is empty or unset in .env" >&2; exit 1; }

docker build -t galaxy-api .
docker rm -f api >/dev/null 2>&1 || true
docker run -d --name api --network galaxynet -p "$HOST_PORT:8000" --restart unless-stopped \
    -e DATABASE_URL="postgresql://galaxy_ro:$GALAXY_RO_PASSWORD@db:5432/glade_sample" \
    galaxy-api >/dev/null

sleep 2
docker logs api --tail 20
curl -fsS "localhost:$HOST_PORT/health" && echo
