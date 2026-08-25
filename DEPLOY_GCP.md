# Deploying Plant Guardian to GCP

The full stack runs on **Cloud Run** with **Cloud SQL (Postgres)** and **Secret Manager**:

```
Browser
  └─> frontend (Next.js, Cloud Run)          https://frontend-<hash>-el.a.run.app
        ├─ /api/plants/*      ─> backend   (FastAPI, Cloud Run) ─> Cloud SQL Postgres
        └─ /api/vacation-mode ─> vacation-mode (FastAPI, Cloud Run)
                                    └─> ai-assistance (FastAPI + Groq LLM, Cloud Run)
```

## Prerequisites

- A GCP project with billing enabled
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated (`gcloud auth login`)
- Docker enabled for Cloud Build (handled by `gcloud builds submit`)
- A [Groq API key](https://console.groq.com/keys)

## One-command deploy

```bash
chmod +x deploy/gcp-deploy.sh

GCP_PROJECT_ID=your-project-id \
GROQ_API_KEY=gsk_your_key \
GCP_REGION=asia-south1 \
./deploy/gcp-deploy.sh
```

The script is idempotent — safe to re-run after changes. It:

1. Enables the required APIs (Cloud Run, Cloud SQL, Secret Manager, Artifact Registry, Cloud Build)
2. Creates the Artifact Registry repo, Cloud SQL instance/database/user
3. Stores `GROQ_API_KEY` in Secret Manager and grants the runtime service account access
4. Builds and deploys each service in dependency order:
   - `ai-assistance` (Groq key injected from Secret Manager)
   - `vacation-mode` (wired to the deployed AI assistant URL)
   - `backend` (attached to Cloud SQL via the `/cloudsql` unix socket; Alembic migrations run on startup)
   - `frontend` (backend/vacation URLs baked into the build — see `deploy/cloudbuild-frontend.yaml`)
5. Prints all four public URLs

## Manual step-by-step

If you prefer doing it yourself, follow the same order as the script — every command in
`deploy/gcp-deploy.sh` maps 1:1 to a manual step. Key details worth knowing:

| Concern | How it is handled |
| --- | --- |
| Database migrations | Backend container entrypoint runs `alembic upgrade head` on boot |
| DB connectivity | `DATABASE_URL=postgresql+psycopg://user:pass@/plant_guardian?host=/cloudsql/PROJECT:REGION:INSTANCE` + `--add-cloudsql-instances` |
| Secrets | `GROQ_API_KEY` never leaves Secret Manager; injected via `--set-secrets` |
| Frontend API URLs | Next.js rewrites are resolved at build time, so `API_URL` / `VACATION_API_URL` are passed as Docker build args during Cloud Build |
| CORS | The browser only talks to the frontend origin (same-origin proxy), so services need no cross-origin access |

## Redeploying a single service

```bash
# Example: backend change
gcloud builds submit ./backend -t REGION-docker.pkg.dev/PROJECT/plant-guardian/backend:latest
gcloud run deploy backend --region REGION --image REGION-docker.pkg.dev/PROJECT/plant-guardian/backend:latest \
  --add-cloudsql-instances PROJECT:REGION:plant-guardian-db \
  --set-env-vars "DATABASE_URL=...,APP_ENV=production"
```

## Cost notes (hackathon scale)

- Cloud Run scales to zero when idle; you pay per request.
- `db-f1-micro` Cloud SQL keeps a small always-on cost (~$7–10/month). Delete everything when done:

```bash
gcloud sql instances delete plant-guardian-db
gcloud run services delete frontend backend vacation-mode ai-assistance --region asia-south1
```
