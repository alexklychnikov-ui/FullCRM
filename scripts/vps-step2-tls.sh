#!/bin/bash
set -eu
cd /opt/FullCRM
sed -i 's/\r$//' .env

# Step 2: TLS
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq certbot >/dev/null 2>&1 || true
mkdir -p /var/www/certbot

cp infra/nginx/fullcrm.acme.conf infra/nginx/fullcrm.conf
docker compose -f docker-compose.prod.yml up -d nginx

sleep 5
certbot certonly --webroot -w /var/www/certbot \
  -d testfullcrm.alexklyvibe.ru \
  --non-interactive --agree-tos -m admin@testfullcrm.alexklyvibe.ru \
  --no-eff-email || certbot certonly --webroot -w /var/www/certbot \
  -d testfullcrm.alexklyvibe.ru --non-interactive --agree-tos --register-unsafely-without-email

cp infra/nginx/fullcrm.tls.conf infra/nginx/fullcrm.conf
docker compose -f docker-compose.prod.yml up -d

# Update URL env vars
for key in WEB_URL API_CORS_ORIGINS NEXT_PUBLIC_API_URL; do
  grep -q "^${key}=" .env && sed -i "s|^${key}=.*|${key}=https://testfullcrm.alexklyvibe.ru|" .env || echo "${key}=https://testfullcrm.alexklyvibe.ru" >> .env
done
# API_CORS_ORIGINS should be just the origin - same as WEB_URL for this setup

docker compose -f docker-compose.prod.yml up -d api web

sleep 15
curl -fsS https://testfullcrm.alexklyvibe.ru/health
echo
curl -fsS -o /dev/null -w "login_https=%{http_code}\n" https://testfullcrm.alexklyvibe.ru/login
curl -fsS -o /dev/null -w "http_redirect=%{http_code}\n" http://testfullcrm.alexklyvibe.ru/health
