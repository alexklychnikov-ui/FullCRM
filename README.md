# FullCRM Platform

FullCRM Platform is a greenfield CRM platform planned around a Next.js frontend, FastAPI backend, PostgreSQL database, Redis-backed worker, Docker Compose, and Nginx reverse proxy.

## Current Status

Iteration I1 Backend skeleton is active. The repository contains the bootstrap scaffold and a minimal FastAPI service with a health endpoint.

## Planned Stack

- Web: Next.js, React, TypeScript, Tailwind
- API: FastAPI, Python
- Database: PostgreSQL
- Background jobs: Redis worker
- Infrastructure: Docker Compose, Nginx

## Local Run

Backend:

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
python -m pytest
python -m uvicorn app.main:app --reload
```

Health check: `GET http://localhost:8000/health`.

Docker Compose currently defines only PostgreSQL and Redis placeholders so infrastructure configuration can be validated independently from the backend.

## Secrets

Do not commit real secrets. Use `.env.example` as a template and keep local values in `.env`.

## Next Iteration

I2 Database migrations/seeds: add PostgreSQL schema foundations when the backend skeleton review is closed.
