#!/usr/bin/env bash
# Deploys Plant Guardian to GCP: 4 Cloud Run services + Cloud SQL Postgres + Secret Manager.
#
# Required environment (or export before running):
#   GCP_PROJECT_ID   your GCP project id
#   GROQ_API_KEY     Groq API key for the AI Care Assistant
# Optional:
#   GCP_REGION       default: asia-south1
#
# Usage:
#   chmod +x deploy/gcp-deploy.sh
#   GCP_PROJECT_ID=my-project GROQ_API_KEY=gsk_... ./deploy/gcp-deploy.sh

set -euo pipefail

cd "$(dirname "$0")/.."

PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID to your GCP project id}"
GROQ_API_KEY_VALUE="${GROQ_API_KEY:?Set GROQ_API_KEY to your Groq API key}"
REGION="${GCP_REGION:-asia-south1}"

REPO="plant-guardian"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}"
SQL_INSTANCE="plant-guardian-db"
SQL_DB="plant_guardian"
SQL_USER="plant_guardian"
SECRET_NAME="groq-api-key"

# Load DB credentials from .env when present.
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a; source .env; set +a
fi
POSTGRES_USER="${POSTGRES_USER:-$SQL_USER}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(openssl rand -hex 16)}"

INSTANCE_CONNECTION="${PROJECT_ID}:${REGION}:${SQL_INSTANCE}"
CLOUDSQL_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@/${SQL_DB}?host=/cloudsql/${INSTANCE_CONNECTION}"

echo "==> Project: ${PROJECT_ID} | Region: ${REGION}"

gcloud config set project "${PROJECT_ID}"

echo "==> Enabling APIs"
gcloud services enable \
  run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com \
  artifactregistry.googleapis.com cloudbuild.googleapis.com

echo "==> Creating Artifact Registry repository (${REPO})"
gcloud artifacts repositories create "${REPO}" \
  --repository-format=docker --location="${REGION}" || echo "    already exists"

echo "==> Creating Cloud SQL instance (${SQL_INSTANCE})"
if ! gcloud sql instances describe "${SQL_INSTANCE}" >/dev/null 2>&1; then
  gcloud sql instances create "${SQL_INSTANCE}" \
    --database-version=POSTGRES_17 \
    --edition=enterprise \
    --tier=db-f1-micro \
    --region="${REGION}" \
    --storage-auto-increase
else
  echo "    already exists"
fi

gcloud sql databases create "${SQL_DB}" --instance="${SQL_INSTANCE}" || echo "    database already exists"
gcloud sql users create "${POSTGRES_USER}" --instance="${SQL_INSTANCE}" --password="${POSTGRES_PASSWORD}" || \
  gcloud sql users set-password "${POSTGRES_USER}" --instance="${SQL_INSTANCE}" --password="${POSTGRES_PASSWORD}"

echo "==> Storing Groq API key in Secret Manager"
printf '%s' "${GROQ_API_KEY_VALUE}" | gcloud secrets create "${SECRET_NAME}" --data-file=- || \
  printf '%s' "${GROQ_API_KEY_VALUE}" | gcloud secrets versions add "${SECRET_NAME}" --data-file=-

PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
echo "==> Granting the Cloud Run service account access to the secret and Cloud SQL"
gcloud secrets add-iam-policy-binding "${SECRET_NAME}" \
  --member="serviceAccount:${COMPUTE_SA}" --role="roles/secretmanager.secretAccessor" >/dev/null
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${COMPUTE_SA}" --role="roles/cloudsql.client" >/dev/null

deploy_service () {
  local name="$1"; shift
  echo "==> Deploying ${name}"
  gcloud run deploy "${name}" "$@" --region="${REGION}" --allow-unauthenticated >/dev/null
  gcloud run services describe "${name}" --region="${REGION}" --format='value(status.url)'
}

echo "==> Building ai-assistance image"
gcloud builds submit ./ai_assistance -t "${REGISTRY}/ai-assistance:latest"
AI_URL="$(deploy_service ai-assistance \
  --image "${REGISTRY}/ai-assistance:latest" \
  --port 8000 --memory 512Mi \
  --set-secrets "GROQ_API_KEY=${SECRET_NAME}:latest")"

echo "==> Building vacation-mode image"
gcloud builds submit ./vacation_mode -t "${REGISTRY}/vacation-mode:latest"
VACATION_URL="$(deploy_service vacation-mode \
  --image "${REGISTRY}/vacation-mode:latest" \
  --port 8001 --memory 512Mi \
  --set-env-vars "AI_ASSISTANCE_URL=${AI_URL}")"

echo "==> Building backend image"
gcloud builds submit ./backend -t "${REGISTRY}/backend:latest"
BACKEND_URL="$(deploy_service backend \
  --image "${REGISTRY}/backend:latest" \
  --port 8000 --memory 512Mi \
  --add-cloudsql-instances "${INSTANCE_CONNECTION}" \
  --set-env-vars "DATABASE_URL=${CLOUDSQL_URL},APP_ENV=production,AUTO_SEED=true,CORS_ORIGINS=*")"

echo "==> Building frontend image (API URLs baked in at build time)"
gcloud builds submit ./frontend --config deploy/cloudbuild-frontend.yaml \
  --substitutions "_API_URL=${BACKEND_URL},_VACATION_API_URL=${VACATION_URL},_IMAGE=${REGISTRY}/frontend:latest"
FRONTEND_URL="$(deploy_service frontend \
  --image "${REGISTRY}/frontend:latest" \
  --port 3000 --memory 512Mi)"

cat <<EOF

============================================================
 Deployment complete
============================================================
 Frontend:      ${FRONTEND_URL}
 Backend API:   ${BACKEND_URL}
 Vacation Mode: ${VACATION_URL}
 AI Assistant:  ${AI_URL}
============================================================
 Database user password: (the POSTGRES_PASSWORD you supplied or a generated one)
 Keep it safe if you need to reconnect manually.

 Redeploying later:
   Re-run this script, or rebuild+redeploy one service, e.g.
   gcloud builds submit ./backend -t ${REGISTRY}/backend:latest
   gcloud run deploy backend --region ${REGION} --image ${REGISTRY}/backend:latest \\
     --add-cloudsql-instances ${INSTANCE_CONNECTION} \\
     --set-env-vars "DATABASE_URL=${CLOUDSQL_URL},APP_ENV=production"
============================================================
EOF
