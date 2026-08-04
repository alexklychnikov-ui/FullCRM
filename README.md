# FullCRM Platform

FullCRM Platform is a greenfield CRM platform planned around a Next.js frontend, FastAPI backend, PostgreSQL database, Redis-backed worker, Docker Compose, and Nginx reverse proxy.

## Current Status

Platform baseline for `apps/api` is in place: FastAPI app factory, auth/runtime config guards, Alembic migrations, demo seed bootstrap, DB session wiring, and health/readiness endpoints.

`apps/web` provides the MVP RU-first web shell with cookie auth against the API (via same-origin BFF routes).

## Planned Stack

- Web: Next.js, React, TypeScript, Tailwind
- API: FastAPI, Python
- Database: PostgreSQL
- Background jobs: Redis worker
- Infrastructure: Docker Compose, Nginx

## Local Run

Web:

```powershell
cd apps/web
npm install
copy ..\\..\\.env.example .env.local
npm run dev
```

Web shell uses cookie auth against the API at `NEXT_PUBLIC_API_URL`. It does not read portfolio UI JSON from `public/data/*`.

Backend:

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
python -m pytest
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

API probes:

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/health/live`
- `GET http://localhost:8000/health/ready`

Demo seed (local/dev only; requires `SEED_DEMO=true` in `.env`; optional `SEED_ADMIN_PASSWORD` enables login):

```powershell
cd apps/api
.\.venv\Scripts\python -m alembic upgrade head
$env:SEED_DEMO="true"
.\.venv\Scripts\python -m app.db.seed
```

Docker Compose backend baseline:

```powershell
docker compose up -d postgres
docker compose run --rm api alembic upgrade head
docker compose up --build api
```

Compose keeps local host defaults in `.env`, then overrides the database hostname to `postgres` for the `api` container at runtime.

For local host-based runs outside Docker, keep `DATABASE_URL` pointed at `127.0.0.1`. Inside Docker Compose the `api` service rewires it to `postgres`.

Production stack (nginx + web + api + postgres + redis):

```powershell
copy .env.prod.example .env
# edit .env: POSTGRES_PASSWORD, JWT_SECRET (32+ chars), WEB_URL, API_CORS_ORIGINS

docker compose -f docker-compose.prod.yml config
docker compose -f docker-compose.prod.yml up -d --build

# probes through nginx
curl http://127.0.0.1/health
curl http://127.0.0.1/api/health/ready
```

VPS (after Docker install): clone repo, create `.env` from `.env.prod.example`, run the same compose file. Optional helper: `scripts/deploy-prod.ps1` or `scripts/deploy-prod.sh`.

Routing: `/` → web, `/api/` → FastAPI, `/health` → API health. Browser calls same-origin `/api/*`; SSR uses internal `http://api:8000`.

Local dev workflow (`docker compose up` for api/postgres only, `npm run dev` for web) is unchanged.

## Secrets

Do not commit real secrets. Use `.env.example` as a template and keep local values in `.env`.

## Next Iteration

Build product APIs on top of the backend baseline without changing the host-vs-compose runtime contract.
