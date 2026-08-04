#!/bin/bash
set -eu
cd /opt/FullCRM
chmod +x scripts/bootstrap-prod-admin.sh scripts/update-prod.sh

grep -q '^BOOTSTRAP_ADMIN_EMAIL=' .env || echo 'BOOTSTRAP_ADMIN_EMAIL=admin@testfullcrm.alexklyvibe.ru' >> .env
grep -q '^BOOTSTRAP_ADMIN_PASSWORD=' .env || echo "BOOTSTRAP_ADMIN_PASSWORD=$(openssl rand -base64 24)" >> .env
grep -q '^BOOTSTRAP_ADMIN=' .env || echo 'BOOTSTRAP_ADMIN=false' >> .env

export BOOTSTRAP_ADMIN=true
export BOOTSTRAP_CONFIRM=yes
set -a
. ./.env
set +a

./scripts/bootstrap-prod-admin.sh

HTTP_CODE=$(curl -sS -o /tmp/login.json -w "%{http_code}" -X POST http://127.0.0.1/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${BOOTSTRAP_ADMIN_EMAIL}\",\"password\":\"${BOOTSTRAP_ADMIN_PASSWORD}\"}")
echo "login_http=${HTTP_CODE}"
python3 -c "import json; d=json.load(open('/tmp/login.json')); print('has_access_token=', 'access_token' in d)"

docker compose -f docker-compose.prod.yml exec -T postgres psql -U fullcrm -d fullcrm -c "SELECT count(*) AS users FROM users; SELECT count(*) AS companies FROM companies; SELECT count(*) AS deals FROM deals;"
