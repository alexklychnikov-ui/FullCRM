#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

git pull --ff-only

if [ -f infra/nginx/fullcrm.tls.conf ]; then
  cp infra/nginx/fullcrm.tls.conf infra/nginx/fullcrm.conf
fi

docker compose -f "$COMPOSE_FILE" up -d --build

echo "Waiting for nginx health..."
deadline=$(( $(date +%s) + 180 ))
while [ "$(date +%s)" -lt "$deadline" ]; do
  if docker compose -f "$COMPOSE_FILE" ps nginx 2>/dev/null | grep -q "(healthy)"; then
    break
  fi
  sleep 5
done

curl -fsS "https://testfullcrm.alexklyvibe.ru/health" || curl -fsS "http://127.0.0.1/health"
echo
echo "Update complete."
