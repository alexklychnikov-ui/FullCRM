#!/usr/bin/env bash
set -eu
cd /opt/FullCRM
set -a
. ./.env
set +a
docker compose -f docker-compose.prod.yml exec -T \
  -e "BOOTSTRAP_ADMIN_EMAIL=${BOOTSTRAP_ADMIN_EMAIL}" \
  -e "BOOTSTRAP_ADMIN_PASSWORD=${BOOTSTRAP_ADMIN_PASSWORD}" \
  api python - <<'PY'
import os
from sqlalchemy import select

from app.auth.passwords import hash_password
from app.db.models import User
from app.db.session import create_db_engine, create_session_factory

email = os.environ["BOOTSTRAP_ADMIN_EMAIL"].strip()
password = os.environ["BOOTSTRAP_ADMIN_PASSWORD"]
engine = create_db_engine()
with create_session_factory(engine)() as session:
    user = session.scalar(select(User).where(User.email == email))
    if user is None:
        raise SystemExit("user_not_found")
    user.password_hash = hash_password(password)
    session.commit()
print("password_sync_ok")
PY
