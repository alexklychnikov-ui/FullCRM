#!/bin/bash
set -eu
cd /opt/FullCRM

# Step 5: merge selected keys from stdin (base64 env chunk) without printing values
if [ -f /tmp/sync-env.txt ]; then
  sed -i 's/\r$//' /tmp/sync-env.txt
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      ''|\#*) continue ;;
      POSTGRES_PASSWORD=*|JWT_SECRET=*|DATABASE_URL=*)
        continue
        ;;
      *)
        key="${line%%=*}"
        val="${line#*=}"
        if grep -q "^${key}=" .env; then
          sed -i "s|^${key}=.*|${key}=${val}|" .env
        else
          echo "${key}=${val}" >> .env
        fi
        ;;
    esac
  done < /tmp/sync-env.txt
  rm -f /tmp/sync-env.txt
fi

sed -i 's/\r$//' .env
docker compose -f docker-compose.prod.yml up -d api web
echo "env_sync=ok"
