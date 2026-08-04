#!/bin/bash
set -eu
cd /opt/FullCRM
set -a
. ./.env
set +a
docker compose -f docker-compose.prod.yml exec -T \
  -e BOOTSTRAP_ADMIN=true \
  -e BOOTSTRAP_CONFIRM=yes \
  -e "BOOTSTRAP_ADMIN_EMAIL=${BOOTSTRAP_ADMIN_EMAIL}" \
  -e "BOOTSTRAP_ADMIN_PASSWORD=${BOOTSTRAP_ADMIN_PASSWORD}" \
  api python -m app.db.bootstrap_prod

HTTP_CODE=$(curl -sS -o /tmp/login.json -w "%{http_code}" -X POST http://127.0.0.1/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${BOOTSTRAP_ADMIN_EMAIL}\",\"password\":\"${BOOTSTRAP_ADMIN_PASSWORD}\"}")
echo "login_http=${HTTP_CODE}"
python3 -c "import json; d=json.load(open('/tmp/login.json')); print('has_access_token=', 'access_token' in d)"
docker compose -f docker-compose.prod.yml exec -T postgres psql -U fullcrm -d fullcrm -c "SELECT count(*) AS users FROM users; SELECT count(*) AS companies FROM companies; SELECT count(*) AS deals FROM deals;"
