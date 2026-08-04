#!/usr/bin/env bash
set -eu
cd /opt/FullCRM

echo "=== STACK ==="
docker compose -f docker-compose.prod.yml ps --format '{{.Name}} {{.Status}}'

echo "=== USERS ==="
docker exec fullcrm-postgres-1 psql -U fullcrm -d fullcrm -tAc 'SELECT count(*) FROM users;'

echo "=== ENV FLAGS ==="
grep -q '^TELEGRAM_BOT_TOKEN=.\+' .env && echo TELEGRAM_BOT_TOKEN=present || echo TELEGRAM_BOT_TOKEN=absent
grep '^TELEGRAM_ENABLED=' .env

echo "=== HTTPS ==="
curl -fsSk -o /dev/null -w 'local_https:%{http_code}\n' https://127.0.0.1/health -H 'Host: testfullcrm.alexklyvibe.ru'

echo "=== GETME ==="
T=$(grep '^TELEGRAM_BOT_TOKEN=' .env | cut -d= -f2- | tr -d '\r')
curl -fsS "https://api.telegram.org/bot${T}/getMe" | python3 -c 'import sys,json;d=json.load(sys.stdin);print("getMe:ok" if d.get("ok") else "getMe:fail");print("bot_username:"+str(d.get("result",{}).get("username","")))'

echo "=== LOGIN ==="
E=$(grep '^BOOTSTRAP_ADMIN_EMAIL=' .env | cut -d= -f2- | tr -d '\r')
P=$(grep '^BOOTSTRAP_ADMIN_PASSWORD=' .env | cut -d= -f2- | tr -d '\r')
rm -f /tmp/cookies.txt
curl -fsSk -c /tmp/cookies.txt -X POST https://127.0.0.1/api/auth/login \
  -H 'Host: testfullcrm.alexklyvibe.ru' \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"${E}\",\"password\":\"${P}\"}" > /tmp/login.json
python3 -c 'import json;d=json.load(open("/tmp/login.json"));print("login:ok" if d.get("user",{}).get("email") else "login:fail")'

echo "=== INTEGRATIONS ==="
curl -fsSk -b /tmp/cookies.txt -H 'Host: testfullcrm.alexklyvibe.ru' https://127.0.0.1/api/communications/integrations/status > /tmp/status.json
python3 -c 'import json;d=json.load(open("/tmp/status.json"));print("telegram_mode:"+str(d.get("telegram",{}).get("mode")))'

echo "=== POLL ==="
C1=$(curl -sSk -b /tmp/cookies.txt -o /tmp/p1.json -w '%{http_code}' -X POST -H 'Host: testfullcrm.alexklyvibe.ru' https://127.0.0.1/api/communications/telegram/poll)
echo "poll1_http:${C1}"
sleep 32
C3=$(curl -sSk -b /tmp/cookies.txt -o /tmp/p3.json -w '%{http_code}' -X POST -H 'Host: testfullcrm.alexklyvibe.ru' https://127.0.0.1/api/communications/telegram/poll)
echo "poll_after_cooldown_http:${C3}"
python3 -c 'import json;d=json.load(open("/tmp/status.json")); t=[i for i in d.get("integrations",[]) if i.get("channel")=="telegram"][0]; print("telegram_mode:"+str(t.get("mode")))'
