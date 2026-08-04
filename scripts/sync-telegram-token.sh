#!/usr/bin/env bash
set -eu
LINE="$(tr -d '\r' < /tmp/tgline.txt)"
KEY="${LINE%%=*}"
VAL="${LINE#*=}"
python3 <<PY
from pathlib import Path
key = "$KEY"
val = """$VAL"""
p = Path("/opt/FullCRM/.env")
lines = p.read_text().splitlines()
out = []
found = False
for line in lines:
    if line.startswith(key + "="):
        out.append(f"{key}={val}")
        found = True
    else:
        out.append(line)
if not found:
    out.append(f"{key}={val}")
p.write_text("\n".join(out) + "\n")
print("token_synced", len(val))
PY
rm -f /tmp/tgline.txt
cd /opt/FullCRM
docker compose -f docker-compose.prod.yml up -d api
sleep 12
docker exec fullcrm-api-1 printenv TELEGRAM_BOT_TOKEN | wc -c
