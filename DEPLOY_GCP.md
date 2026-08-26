# Deploying Plant Guardian to GCP

The full stack runs on **Cloud Run** with **Cloud SQL (Postgres)**, **Pub/Sub**,
**Cloud Scheduler**, and **Secret Manager**:

```
Browser
  └─> frontend (Next.js, Cloud Run)          https://frontend-<hash>-el.a.run.app
        ├─ /api/plants/*      ─> backend   (FastAPI, Cloud Run) ─> Cloud SQL Postgres
        └─ /api/vacation-mode ─> vacation-mode (FastAPI, Cloud Run)
                                    └─> ai-assistance (FastAPI + Groq LLM, Cloud Run)

Cloud Scheduler (OIDC: plant-guardian-scheduler)
  └─> backend /internal/notifications/dispatch
        └─> Pub/Sub topic
              └─> authenticated push (OIDC: plant-guardian-pubsub-push)
                    └─> backend /internal/notifications/pubsub ─> browser Web Push
```

## Prerequisites

- A GCP project with billing enabled
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated (`gcloud auth login`)
- Docker enabled for Cloud Build (handled by `gcloud builds submit`)
- A [Groq API key](https://console.groq.com/keys)
- A VAPID key pair for browser push (`npx web-push generate-vapid-keys`) if notifications are enabled

## One-command deploy

```bash
chmod +x deploy/gcp-deploy.sh

GCP_PROJECT_ID=your-project-id \
GROQ_API_KEY=gsk_your_key \
VAPID_PUBLIC_KEY=your_public_key \
VAPID_PRIVATE_KEY=your_private_key \
VAPID_SUBJECT=mailto:you@example.com \
GCP_REGION=asia-south1 \
./deploy/gcp-deploy.sh
```

The script is idempotent — safe to re-run after changes. It:

1. Enables the required APIs (Cloud Run, Cloud SQL, Secret Manager, Artifact Registry,
   Cloud Build, Cloud Scheduler, Pub/Sub, IAM, and IAM Credentials)
2. Creates the Artifact Registry repo, Cloud SQL instance/database/user
3. Creates six dedicated service accounts and applies least-privilege IAM bindings
4. Stores `GROQ_API_KEY` and the optional VAPID private key in Secret Manager
5. Builds and deploys each service in dependency order:
   - `ai-assistance` (Groq key injected from Secret Manager)
   - `vacation-mode` (wired to the deployed AI assistant URL)
   - `backend` (attached to Cloud SQL via the `/cloudsql` unix socket; Alembic migrations run on startup)
   - `frontend` (backend/vacation URLs baked into the build — see `deploy/cloudbuild-frontend.yaml`)
6. Prints all four public URLs

When both VAPID keys are supplied, the script creates the Pub/Sub topic and authenticated
push subscription, grants the backend publish-only access, and creates a Scheduler job that
scans for reminders every 15 minutes. Scheduler and Pub/Sub each call the backend using a
different Google-signed OIDC identity. Notification delivery records make repeated scans and
Pub/Sub redelivery idempotent. Transient Web Push failures return a non-success status so
Pub/Sub retries with backoff; expired browser subscriptions are discarded without retry.

If the VAPID keys are omitted, the rest of the product deploys normally and Pub/Sub reminder
infrastructure is skipped. Local Docker Compose remains independent of GCP: with the Pub/Sub
variables blank, the backend uses its existing direct Web Push delivery path.

## IAM and service identities

The deployment no longer uses the default Compute Engine service account at runtime.

| Identity | Attached to | Granted access |
| --- | --- | --- |
| `plant-guardian-frontend` | Frontend Cloud Run service | No project roles |
| `plant-guardian-backend` | Backend Cloud Run service | Cloud SQL Client, Pub/Sub Publisher on one topic, VAPID secret accessor |
| `plant-guardian-vacation` | Vacation Mode Cloud Run service | No project roles |
| `plant-guardian-ai` | AI Assistance Cloud Run service | Groq secret accessor only |
| `plant-guardian-scheduler` | Cloud Scheduler OIDC caller | Cloud Run Invoker on backend |
| `plant-guardian-pubsub-push` | Pub/Sub push OIDC caller | Cloud Run Invoker on backend |

The Pub/Sub service agent receives Service Account Token Creator on only the Pub/Sub push
identity. The account running the deployment receives Service Account User on these six
identities so `gcloud` can attach/use them.

## Manual step-by-step

If you prefer doing it yourself, follow the same order as the script — every command in
`deploy/gcp-deploy.sh` maps 1:1 to a manual step. Key details worth knowing:

| Concern | How it is handled |
| --- | --- |
| Database migrations | Backend container entrypoint runs `alembic upgrade head` on boot |
| DB connectivity | `DATABASE_URL=postgresql+psycopg://user:pass@/plant_guardian?host=/cloudsql/PROJECT:REGION:INSTANCE` + `--add-cloudsql-instances` |
| Secrets | `GROQ_API_KEY` and the VAPID private key are injected from Secret Manager |
| Reminder queue | The backend publishes a compact delivery ID; plant and subscription data remain in PostgreSQL |
| Push authentication | Scheduler and Pub/Sub JWT signatures, audience, verified email, and email-verification claim are checked by the backend |
| Frontend API URLs | Next.js rewrites are resolved at build time, so `API_URL` / `VACATION_API_URL` are passed as Docker build args during Cloud Build |
| CORS | The browser only talks to the frontend origin (same-origin proxy), so services need no cross-origin access |

## Redeploying a single service

```bash
# Example: backend change
gcloud builds submit ./backend -t REGION-docker.pkg.dev/PROJECT/plant-guardian/backend:latest
gcloud run deploy backend --region REGION --image REGION-docker.pkg.dev/PROJECT/plant-guardian/backend:latest \
  --service-account plant-guardian-backend@PROJECT.iam.gserviceaccount.com \
  --add-cloudsql-instances PROJECT:REGION:plant-guardian-db \
  --set-env-vars "DATABASE_URL=...,APP_ENV=production"
```

For normal updates, re-run the deployment script so the Pub/Sub endpoint, audiences, IAM
bindings, and service identities stay synchronized.

## Verify IAM and Pub/Sub after deployment

```bash
gcloud run services describe backend --region "$GCP_REGION" \
  --format='value(spec.template.spec.serviceAccountName)'

gcloud pubsub topics describe plant-care-notifications
gcloud pubsub subscriptions describe plant-care-notifications-push

gcloud scheduler jobs run plant-guardian-notifications --location "$GCP_REGION"
```

The backend logs should show a Scheduler scan followed by an authenticated Pub/Sub push when
a subscribed browser has a plant due in its configured reminder window.

## Cost notes (hackathon scale)

- Cloud Run scales to zero when idle; you pay per request.
- Scheduler and Pub/Sub add usage-based costs; at this reminder volume they remain small, but
  billing and free-tier limits should still be reviewed for the selected region.
- `db-f1-micro` Cloud SQL keeps a small always-on cost (~$7–10/month). Delete everything when done:

```bash
gcloud sql instances delete plant-guardian-db
gcloud run services delete frontend backend vacation-mode ai-assistance --region asia-south1
```
