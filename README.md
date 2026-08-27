# Plant Guardian

Plant Guardian is a complete plant-watering dashboard that turns a watering schedule into a clear urgency score. It helps houseplant owners see which plants are comfortable, which need water soon, and which are at high risk.

The product message is simple: **Most trackers tell you good or bad. Plant Guardian tells you how urgent.**

## Problem statement

Houseplant care information is often spread across notes, calendars, and memory. A date alone does not answer the most useful question: which plant needs attention first? Plant Guardian stores a plant's schedule and watering history, then calculates comparable care urgency on every API response.

## Differentiator: Plant Risk Score

The FastAPI backend calculates the score dynamically. It is never stored in PostgreSQL, so it cannot become stale.

```text
risk score = min(100, (days since watered / watering frequency) * 100)
```

The result is rounded to an integer and mapped to these states:

| Score | Status | Visual state |
| --- | --- | --- |
| 0-39 | Healthy | Green |
| 40-69 | Needs Water Soon | Amber |
| 70-100 | Overdue / High Risk | Red |

`days_since_watered` uses calendar-day difference in UTC. `days_until_due` is the watering frequency minus that value. A negative value means the plant is overdue.

## Features

- Full create, read, update, and delete flows
- Account signup, login, logout, profile editing, household location, and required pet profile
- Backend-calculated risk score, status, days since watered, and days until due
- `Just Watered` action with an immediate in-place dashboard update
- Account-wide growth avatar with XP, mood, and a garden streak: a week advances only when at least 70% of plants are cared for and no plant is overdue
- Plant-specific care intervals from the bundled catalog, with a 7-day fallback for unknown species
- Curated pet-safety resolution with cat/dog flags, placement guidance, dashboard filters, and vacation handling warnings
- Tropical-India seasonal cadence with transparent base/effective frequencies and a development-only season simulator
- Append-only care history for watering, soil checks, fertilizing, misting, pruning, and repotting
- Opt-in browser push reminders for plants that are due or overdue, with configurable local delivery time
- **AI Care Assistant** (Groq LLM) that turns care data into clear caretaker instructions
- **Vacation Mode**: pick dates and plants, get a watering schedule plus an AI-written caretaker briefing you can copy and share
- Dynamic room filters created only from existing plant records
- Nickname and species search that combines with room filtering
- Highest risk, lowest risk, recently watered, and name sorting
- Dashboard totals for healthy, soon, and high-risk plants
- Three-stage plant cards: care status, plant profile/fun facts, and a practical growing guide
- Smooth GSAP card-flip transitions with keyboard controls and a reduced-motion fallback
- Expandable care notes
- Form validation, delete confirmation, error recovery, skeleton loading, and toast feedback
- Responsive layout and keyboard-accessible controls
- Twenty-two idempotently seeded plant profiles covering all risk, growth, mood, and pet-safety states
- PostgreSQL schema migrations with Alembic
- Containerized frontend, backend, database, and both AI services
- One-command GCP deployment with Cloud Run, Cloud SQL, Pub/Sub, Scheduler, Secret Manager, and dedicated IAM identities (`deploy/gcp-deploy.sh`)

## Architecture

```text
Browser
  └─> Next.js App Router dashboard (same-origin /api proxy)
        ├─ /api/auth/*         -> backend FastAPI   -> SQLAlchemy -> PostgreSQL
        ├─ /api/plants/*       -> backend FastAPI   -> SQLAlchemy -> PostgreSQL
        └─ /api/vacation-mode  -> vacation-mode FastAPI
                                     └─> ai-assistance FastAPI -> Groq LLM
```

The browser calls relative `/api` routes. Next.js proxies plant requests to `API_URL` and
vacation requests to `VACATION_API_URL`, keeping production addresses out of the client
bundle. Vacation Mode composes the two backend features: it builds the schedule itself and
delegates the natural-language caretaker message to the AI Care Assistant. If the LLM is
unreachable, a deterministic caretaker message preserves the seasonal and pet warnings.

## Technology stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS, GSAP, Phosphor Icons
- Backend: Python, FastAPI, Pydantic, SQLAlchemy
- AI services: Python, FastAPI, Groq SDK (Llama 3.x), httpx service-to-service calls
- Database: PostgreSQL
- Migrations: Alembic
- Tests: Pytest, FastAPI TestClient, Vitest
- Deployment: Docker Compose locally; Cloud Run + Cloud SQL + Pub/Sub + Secret Manager on GCP

## Folder structure

```text
plant-guardian/
├── frontend/
│   ├── app/
│   ├── components/
│   │   ├── dashboard/
│   │   ├── plants/
│   │   ├── vacation/
│   │   └── ui/
│   ├── lib/
│   ├── services/
│   ├── types/
│   ├── Dockerfile
│   └── package.json
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── core/
│   │   ├── database/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── schemas/
│   │   └── services/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── ai_assistance/           # AI Care Assistant (Groq LLM)
├── vacation_mode/           # Vacation planner, calls ai_assistance
├── deploy/                  # GCP deployment script + Cloud Build config
├── DEPLOY_GCP.md            # Cloud Run deployment guide
├── .env.example
├── docker-compose.yml
└── README.md
```

## Quick start with Docker

Requirements: Docker Engine with Docker Compose.

1. Copy the example environment file.

   ```powershell
   Copy-Item .env.example .env
   ```

2. Replace `POSTGRES_PASSWORD` and the password inside `DATABASE_URL` with the same strong local password, and paste your [Groq API key](https://console.groq.com/keys) into `GROQ_API_KEY`.

3. Build and start the application.

   ```bash
   docker compose up --build
   ```

4. Open [http://localhost:3000](http://localhost:3000).

The backend entrypoint applies migrations before startup. With `AUTO_SEED=true`, it
  synchronizes the bundled 22-plant catalog without duplicating records or deleting user
plants. Matching existing plants receive the new profile and care-guide content. Local
service ports: backend `8000`, AI assistant `8001`, vacation mode `8002`. API
documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs)
when `APP_ENV` is not `production`.

Stop the stack with:

```bash
docker compose down
```

Add `-v` only when you intentionally want to remove the PostgreSQL volume and all application data.

## Local installation

### Requirements

- Node.js 20.9 or newer
- Python 3.11 or newer
- PostgreSQL 15 or newer

### Environment variables

Copy `.env.example` to `.env` and set these values:

| Variable | Purpose | Example for local development |
| --- | --- | --- |
| `POSTGRES_DB` | Docker database name | `plant_guardian` |
| `POSTGRES_USER` | Docker database role | `plant_guardian` |
| `POSTGRES_PASSWORD` | Docker database password | Use a strong local value |
| `DATABASE_URL` | SQLAlchemy connection string | `postgresql+psycopg://user:password@localhost:5432/database` |
| `APP_ENV` | Controls development-only API docs | `development` |
| `CORS_ORIGINS` | Comma-separated allowed browser origins | `http://localhost:3000` |
| `AUTO_SEED` | Seeds an empty database in Docker | `true` |
| `SEED_STARTER_PLANTS` | Gives each new account the demo garden | `true` for demos |
| `SESSION_LIFETIME_DAYS` | Opaque login-session lifetime | `7` |
| `VAPID_PUBLIC_KEY` | Public Web Push application-server key | Generated VAPID public key |
| `VAPID_PRIVATE_KEY` | Private Web Push key; keep secret | Generated VAPID private key |
| `VAPID_SUBJECT` | Web Push administrator contact | `mailto:you@example.com` |
| `NOTIFICATION_DISPATCH_TOKEN` | Protects the scheduled dispatch endpoint | A long random value |
| `GCP_PROJECT_ID` | Enables the Pub/Sub publisher with the topic settings below | Set automatically by the GCP script |
| `PUBSUB_NOTIFICATION_TOPIC` | Topic used for asynchronous reminder jobs | Set automatically by the GCP script |
| `PUBSUB_PUSH_SERVICE_ACCOUNT` / `PUBSUB_PUSH_AUDIENCE` | Expected authenticated Pub/Sub caller | Set automatically by the GCP script |
| `SCHEDULER_SERVICE_ACCOUNT` / `SCHEDULER_AUDIENCE` | Expected authenticated Scheduler caller | Set automatically by the GCP script |
| `API_URL` | Server-side FastAPI URL used by Next.js | `http://localhost:8000` |
| `VACATION_API_URL` | Server-side vacation-mode URL used by Next.js | `http://localhost:8002` |
| `GROQ_API_KEY` | Groq API key for the AI Care Assistant | `gsk_...` |
| `GROQ_MODEL` | Groq model id | `llama-3.1-8b-instant` |
| `AI_ASSISTANCE_URL` | Vacation mode -> AI assistant URL (non-Compose runs) | `http://localhost:8001` |
| `GOOGLE_CLIENT_ID` | Backend audience used to verify Google ID tokens | Google Web client ID |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Browser Google Identity Services client ID | Same Google Web client ID |

No production URL or credential is committed. Set these through your deployment platform's secret and environment configuration.

### Enable Google sign-in

Create a Web OAuth client in Google Cloud Console and add `http://localhost:3000` to its authorised JavaScript origins. Set the same client ID in `GOOGLE_CLIENT_ID` and `NEXT_PUBLIC_GOOGLE_CLIENT_ID`, then rebuild the frontend. Email/password authentication remains available. New Google accounts are asked for the same name, place, and pets profile details before the account is created.

### Enable browser push reminders

Generate a VAPID key pair once for each environment:

```bash
npx web-push generate-vapid-keys
```

Copy the generated public and private values into `.env` as `VAPID_PUBLIC_KEY` and
`VAPID_PRIVATE_KEY`, set `VAPID_SUBJECT` to a monitored `mailto:` address, and set a
long random `NOTIFICATION_DISPATCH_TOKEN`. Restart the backend and frontend, then use
the **Enable reminders** control on the dashboard. The **Test** button sends immediately.

Automatic reminders are scanned by `POST /internal/notifications/dispatch`. On GCP,
Cloud Scheduler calls that endpoint using its dedicated OIDC identity, the backend queues
one idempotent event per reminder in Pub/Sub, and an authenticated push subscription calls
`POST /internal/notifications/pubsub` to perform Web Push delivery. For local testing,
Pub/Sub is optional and the scan delivers directly when called with the configured token:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/internal/notifications/dispatch `
  -Headers @{ "X-Notification-Token" = $env:NOTIFICATION_DISPATCH_TOKEN }
```

Notification permission must be requested by a user action. Production Web Push also
requires HTTPS; browsers permit `localhost` as a development exception.

### PostgreSQL setup

Create a database and role with values that match `DATABASE_URL`, or start only PostgreSQL through Docker:

```bash
docker compose up database -d
```

### Run the backend

From `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:DATABASE_URL = "postgresql+psycopg://user:password@localhost:5432/plant_guardian"
alembic upgrade head
python -m app.database.seed
uvicorn app.main:app --reload
```

On macOS or Linux, activate the environment with `source .venv/bin/activate` and export `DATABASE_URL` in the shell.

### Run the frontend

From `frontend/`:

```bash
npm install
npm run dev
```

If the backend is not at `http://localhost:8000`, set `API_URL` in `frontend/.env.local` before starting Next.js.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Database-aware service health |
| `GET` | `/api/plants` | List plants, highest risk first |
| `GET` | `/api/plants?room=Office` | Filter plants by room |
| `GET` | `/api/plants?season=winter` | Override the seasonal model for demonstrations |
| `GET` | `/api/plants/{id}` | Get one plant |
| `POST` | `/api/plants` | Create a plant |
| `PUT` | `/api/plants/{id}` | Replace all editable fields |
| `PATCH` | `/api/plants/{id}` | Update selected fields |
| `DELETE` | `/api/plants/{id}` | Delete a plant |
| `POST` | `/api/plants/{id}/water` | Set `last_watered` to the current UTC time |
| `POST` | `/api/auth/signup` | Create an account and household profile |
| `POST` | `/api/auth/login` | Start an HttpOnly cookie session |
| `POST` | `/api/auth/logout` | End the current session |
| `GET/PATCH` | `/api/auth/me` | Read or update the current profile |
| `GET` | `/api/plants/{id}/events` | List the plant's care history, newest first |
| `POST` | `/api/plants/{id}/events` | Record watering or another care action |
| `GET` | `/api/notifications/config` | Get Web Push availability and public VAPID key |
| `POST` | `/api/notifications/subscriptions` | Register or update this browser's reminder settings |
| `DELETE` | `/api/notifications/subscriptions` | Remove a browser push subscription |
| `POST` | `/api/notifications/test` | Send a test notification to a registered browser |
| `POST` | `/internal/notifications/dispatch` | Authenticated due-reminder scan (Scheduler or local token) |
| `POST` | `/internal/notifications/pubsub` | Authenticated Pub/Sub push worker |

### AI services (reached through the same `/api` proxy)

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/vacation-mode` | Full plan: watering schedule + AI caretaker message |
| `POST` | `/api/vacation-mode/plan-only` | Schedule without the LLM call |

Internal service endpoints (`ai-assistance:8000`): `POST /generate-care-instruction`, `POST /generate-vacation-care`, `GET /health`.

Every plant response includes persisted fields plus:

```json
{
  "days_since_watered": 4,
  "days_until_due": 3,
  "risk_score": 57,
  "status": "Needs Water Soon",
  "xp": 75,
  "growth_stage": 3,
  "mood": "doubtful",
  "current_streak": 5,
  "consistency_pct": 100,
  "pet_safety": "toxic",
  "season": "Monsoon",
  "base_watering_frequency": 7,
  "effective_watering_frequency": 9
}
```

Validation failures use FastAPI's structured `422` response. Missing records return `404`. Database failures return a generic `503` message and do not expose stack traces.

## Tests and quality checks

Backend tests use an isolated in-memory database and cover auth, risk and season boundaries, streak math, XP, pet-safety resolution, CRUD, cascade deletion, and watering resets.

```powershell
cd backend
$env:DATABASE_URL = "sqlite+pysqlite:///:memory:"
python -m pytest
```

Frontend tests cover combined querying, sorting, dynamic room derivation, and API method contracts.

```bash
cd frontend
npm test
npm run lint
npm run build
```

## Production configuration

- Use a managed PostgreSQL instance and require encrypted transport in `DATABASE_URL`.
- Set `APP_ENV=production` to disable interactive API documentation.
- Set only the deployed frontend origins in `CORS_ORIGINS`.
- Set `AUTO_SEED=false` unless a demo environment intentionally needs seed records.
- Terminate TLS at the platform load balancer or reverse proxy.
- Run Alembic migrations as a release step when the platform separates release and runtime commands.
- Keep the backend stateless and scale it horizontally behind the platform service.

## Deploy to GCP

The project ships with an automated Cloud Run deployment: four services (frontend,
backend, vacation-mode, ai-assistance), Cloud SQL Postgres, Pub/Sub push delivery,
Cloud Scheduler, Secret Manager, and six dedicated least-privilege service accounts.

```bash
GCP_PROJECT_ID=your-project-id \
GROQ_API_KEY=gsk_your_key \
./deploy/gcp-deploy.sh
```

See [DEPLOY_GCP.md](DEPLOY_GCP.md) for the architecture, manual steps, redeploying a
single service, teardown, and cost notes.

## CI/CD

The repository includes Google Cloud Build pipelines for pull-request validation and
automatic deployment from `main`. Pull requests run backend tests plus frontend tests,
lint, and a production build. Path-filtered deployment triggers build and update only
the services changed by a successful merge, without recreating the database or supporting
GCP resources.

See [CI_CD_SETUP.md](CI_CD_SETUP.md) for the one-time GitHub connection, trigger setup,
permissions, daily workflow, and monitoring instructions.

