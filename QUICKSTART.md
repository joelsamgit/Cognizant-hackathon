# Quick Start — Run Plant Guardian Locally

The fastest way to run the whole product is Docker Compose. One command starts
everything: database, backend, AI assistant, vacation mode, and frontend.

## What you need

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose plugin)
- A [Groq API key](https://console.groq.com/keys) (free account works)

## 1. Get the code

```bash
git clone https://github.com/joelsamgit/Cognizant-hackathon.git
cd Cognizant-hackathon
```

## 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and set two things:

| Variable | What to put |
| --- | --- |
| `POSTGRES_PASSWORD` | any strong password (also used inside `DATABASE_URL`) |
| `GROQ_API_KEY` | your key from console.groq.com |

Everything else can stay as-is for local development.

## 3. Start everything

```bash
docker compose up --build
```

First build takes a few minutes. When it settles, open:

> ### http://localhost:3000

## What runs where

| URL | Service |
| --- | --- |
| http://localhost:3000 | **Frontend** — the dashboard (use this) |
| http://localhost:8000 | Backend API (plants CRUD, risk scores) |
| http://localhost:8001 | AI Care Assistant (Groq LLM) |
| http://localhost:8002 | Vacation Mode service |
| localhost:5432 | PostgreSQL |

If port `8000` is already used by another project on your machine, create a
`docker-compose.override.yml` that maps the backend elsewhere (see the file in this repo
as an example) — nothing else changes, the frontend talks to services internally.

## Things to try

1. **Add a plant** — "Add Plant" button; risk score and status are computed by the backend.
2. **Water a plant** — "Just Watered" resets its timer instantly.
3. **Vacation Mode** — pick dates, select plants, set water amounts, generate.
   You'll get a watering schedule plus an AI-written caretaker message you can copy
   and send to whoever waters your plants.

## Stop / reset

```bash
docker compose down        # stop everything (data survives)
docker compose down -v     # stop AND wipe the database
```

## Running without Docker (development)

- **Backend**: see README.md → "Local installation"
- **Frontend**: `cd frontend && npm install && npm run dev`
- **AI services**: each folder has its own `requirements.txt`; run
  `uvicorn app.main:app --reload` with the env vars from `.env.example`

## Deploying to GCP

See [DEPLOY_GCP.md](DEPLOY_GCP.md) — one script deploys all four Cloud Run services
plus Cloud SQL.
