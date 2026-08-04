#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  echo "Missing .env. Copy .env.prod.example to .env and set secrets first." >&2
  exit 1
fi

docker compose -f docker-compose.prod.yml config >/dev/null
docker compose -f docker-compose.prod.yml up -d --build

echo "Waiting for nginx health..."
deadline=$(( $(date +%s) + 180 ))
while [ "$(date +%s)" -lt "$deadline" ]; do
  if docker compose -f docker-compose.prod.yml ps nginx | grep -q "(healthy)"; then
    break
  fi
  sleep 5
done

curl -fsS "http://127.0.0.1:${NGINX_HTTP_PORT:-80}/health"
echo
curl -fsS -o /dev/null -w "web login HTTP %{http_code}\n" "http://127.0.0.1:${NGINX_HTTP_PORT:-80}/login"
curl -fsS -o /dev/null -w "api via nginx HTTP %{http_code}\n" "http://127.0.0.1:${NGINX_HTTP_PORT:-80}/api/health/ready"

echo "Deploy smoke checks passed."
