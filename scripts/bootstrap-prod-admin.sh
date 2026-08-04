#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

if [ ! -f .env ]; then
  echo "Missing .env in $ROOT_DIR" >&2
  exit 1
fi

# shellcheck disable=SC1091
set -a
. ./.env
set +a

if [ "${BOOTSTRAP_ADMIN:-false}" != "true" ]; then
  echo "Set BOOTSTRAP_ADMIN=true in .env before running." >&2
  exit 1
fi

if [ -z "${BOOTSTRAP_ADMIN_EMAIL:-}" ] || [ -z "${BOOTSTRAP_ADMIN_PASSWORD:-}" ]; then
  echo "Set BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD in .env." >&2
  exit 1
fi

docker compose -f "$COMPOSE_FILE" exec \
  -e BOOTSTRAP_ADMIN=true \
  -e "BOOTSTRAP_CONFIRM=${BOOTSTRAP_CONFIRM:-}" \
  -e "BOOTSTRAP_ADMIN_TOKEN=${BOOTSTRAP_ADMIN_TOKEN:-}" \
  -e "BOOTSTRAP_SUPPLIED_TOKEN=${BOOTSTRAP_SUPPLIED_TOKEN:-}" \
  -e "BOOTSTRAP_ADMIN_EMAIL=${BOOTSTRAP_ADMIN_EMAIL}" \
  -e "BOOTSTRAP_ADMIN_PASSWORD=${BOOTSTRAP_ADMIN_PASSWORD}" \
  -e "BOOTSTRAP_ORG_SLUG=${BOOTSTRAP_ORG_SLUG:-main}" \
  -e "BOOTSTRAP_ORG_NAME=${BOOTSTRAP_ORG_NAME:-FullCRM}" \
  api python -m app.db.bootstrap_prod

echo "Verify login:"
echo "  curl -sS -X POST http://127.0.0.1/api/auth/login \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"email\":\"${BOOTSTRAP_ADMIN_EMAIL}\",\"password\":\"<from .env>\"}'"
