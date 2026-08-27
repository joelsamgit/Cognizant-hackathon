#!/usr/bin/env bash
# Deploys Plant Guardian to GCP with least-privilege service identities and
# asynchronous Pub/Sub push delivery for care notifications.
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

# Load project settings and secrets from the repository environment file when present.
if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
  echo "Set GCP_PROJECT_ID or configure an active gcloud project." >&2
  exit 1
fi
GROQ_API_KEY_VALUE="${GROQ_API_KEY:?Set GROQ_API_KEY in .env or the shell environment}"
GOOGLE_CLIENT_ID_VALUE="${NEXT_PUBLIC_GOOGLE_CLIENT_ID:-${GOOGLE_CLIENT_ID:-}}"
REGION="${GCP_REGION:-asia-south1}"

REPO="plant-guardian"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}"
SQL_INSTANCE="plant-guardian-db"
SQL_DB="plant_guardian"
SQL_USER="plant_guardian"
SECRET_NAME="groq-api-key"
VAPID_SECRET_NAME="plant-guardian-vapid-private-key"
PUBSUB_TOPIC="plant-care-notifications"
PUBSUB_SUBSCRIPTION="plant-care-notifications-push"

AI_SA_NAME="plant-guardian-ai"
VACATION_SA_NAME="plant-guardian-vacation"
BACKEND_SA_NAME="plant-guardian-backend"
FRONTEND_SA_NAME="plant-guardian-frontend"
SCHEDULER_SA_NAME="plant-guardian-scheduler"
PUBSUB_PUSH_SA_NAME="plant-guardian-pubsub-push"

POSTGRES_USER="${POSTGRES_USER:-$SQL_USER}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(openssl rand -hex 16)}"
VAPID_PUBLIC_KEY_VALUE="${VAPID_PUBLIC_KEY:-}"
VAPID_PRIVATE_KEY_VALUE="${VAPID_PRIVATE_KEY:-}"
VAPID_SUBJECT_VALUE="${VAPID_SUBJECT:-mailto:admin@example.com}"

NOTIFICATIONS_CONFIGURED=false
if [[ -n "${VAPID_PUBLIC_KEY_VALUE}" || -n "${VAPID_PRIVATE_KEY_VALUE}" ]]; then
  if [[ -z "${VAPID_PUBLIC_KEY_VALUE}" || -z "${VAPID_PRIVATE_KEY_VALUE}" ]]; then
    echo "VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY must either both be set or both be empty." >&2
    exit 1
  fi
  NOTIFICATIONS_CONFIGURED=true
fi

INSTANCE_CONNECTION="${PROJECT_ID}:${REGION}:${SQL_INSTANCE}"
CLOUDSQL_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@/${SQL_DB}?host=/cloudsql/${INSTANCE_CONNECTION}"

echo "==> Project: ${PROJECT_ID} | Region: ${REGION}"

gcloud config set project "${PROJECT_ID}"

echo "==> Enabling APIs"
gcloud services enable \
  run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com \
  artifactregistry.googleapis.com cloudbuild.googleapis.com cloudscheduler.googleapis.com \
  pubsub.googleapis.com iam.googleapis.com iamcredentials.googleapis.com

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

if [[ "${NOTIFICATIONS_CONFIGURED}" == "true" ]]; then
  echo "==> Storing the VAPID private key in Secret Manager"
  printf '%s' "${VAPID_PRIVATE_KEY_VALUE}" | gcloud secrets create "${VAPID_SECRET_NAME}" --data-file=- || \
    printf '%s' "${VAPID_PRIVATE_KEY_VALUE}" | gcloud secrets versions add "${VAPID_SECRET_NAME}" --data-file=-
fi

PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"
SERVICE_ACCOUNT_DOMAIN="${PROJECT_ID}.iam.gserviceaccount.com"
AI_SA="${AI_SA_NAME}@${SERVICE_ACCOUNT_DOMAIN}"
VACATION_SA="${VACATION_SA_NAME}@${SERVICE_ACCOUNT_DOMAIN}"
BACKEND_SA="${BACKEND_SA_NAME}@${SERVICE_ACCOUNT_DOMAIN}"
FRONTEND_SA="${FRONTEND_SA_NAME}@${SERVICE_ACCOUNT_DOMAIN}"
SCHEDULER_SA="${SCHEDULER_SA_NAME}@${SERVICE_ACCOUNT_DOMAIN}"
PUBSUB_PUSH_SA="${PUBSUB_PUSH_SA_NAME}@${SERVICE_ACCOUNT_DOMAIN}"
PUBSUB_SERVICE_AGENT="service-${PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com"

create_service_account () {
  local account_id="$1"
  local display_name="$2"
  if gcloud iam service-accounts describe "${account_id}@${SERVICE_ACCOUNT_DOMAIN}" >/dev/null 2>&1; then
    echo "    ${account_id} already exists"
  else
    gcloud iam service-accounts create "${account_id}" --display-name "${display_name}"
  fi
}

echo "==> Creating dedicated service accounts"
create_service_account "${AI_SA_NAME}" "Plant Guardian AI runtime"
create_service_account "${VACATION_SA_NAME}" "Plant Guardian vacation runtime"
create_service_account "${BACKEND_SA_NAME}" "Plant Guardian backend runtime"
create_service_account "${FRONTEND_SA_NAME}" "Plant Guardian frontend runtime"
create_service_account "${SCHEDULER_SA_NAME}" "Plant Guardian Scheduler caller"
create_service_account "${PUBSUB_PUSH_SA_NAME}" "Plant Guardian Pub/Sub push caller"

DEPLOYER_ACCOUNT="$(gcloud config get-value account)"
if [[ "${DEPLOYER_ACCOUNT}" == *".gserviceaccount.com" ]]; then
  DEPLOYER_MEMBER="serviceAccount:${DEPLOYER_ACCOUNT}"
else
  DEPLOYER_MEMBER="user:${DEPLOYER_ACCOUNT}"
fi
for service_account in \
  "${AI_SA}" "${VACATION_SA}" "${BACKEND_SA}" "${FRONTEND_SA}" \
  "${SCHEDULER_SA}" "${PUBSUB_PUSH_SA}"; do
  gcloud iam service-accounts add-iam-policy-binding "${service_account}" \
    --member="${DEPLOYER_MEMBER}" --role="roles/iam.serviceAccountUser" >/dev/null
done

echo "==> Applying least-privilege IAM bindings"
gcloud secrets add-iam-policy-binding "${SECRET_NAME}" \
  --member="serviceAccount:${AI_SA}" --role="roles/secretmanager.secretAccessor" >/dev/null
if [[ "${NOTIFICATIONS_CONFIGURED}" == "true" ]]; then
  gcloud secrets add-iam-policy-binding "${VAPID_SECRET_NAME}" \
    --member="serviceAccount:${BACKEND_SA}" --role="roles/secretmanager.secretAccessor" >/dev/null
fi
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${BACKEND_SA}" --role="roles/cloudsql.client" >/dev/null

if [[ "${NOTIFICATIONS_CONFIGURED}" == "true" ]]; then
  if ! gcloud pubsub topics describe "${PUBSUB_TOPIC}" >/dev/null 2>&1; then
    gcloud pubsub topics create "${PUBSUB_TOPIC}"
  fi
  gcloud pubsub topics add-iam-policy-binding "${PUBSUB_TOPIC}" \
    --member="serviceAccount:${BACKEND_SA}" --role="roles/pubsub.publisher" >/dev/null
  gcloud iam service-accounts add-iam-policy-binding "${PUBSUB_PUSH_SA}" \
    --member="serviceAccount:${PUBSUB_SERVICE_AGENT}" \
    --role="roles/iam.serviceAccountTokenCreator" >/dev/null
fi

deploy_service () {
  local name="$1"
  local service_account="$2"
  shift 2
  echo "==> Deploying ${name}" >&2
  gcloud run deploy "${name}" "$@" \
    --region="${REGION}" \
    --service-account="${service_account}" \
    --allow-unauthenticated >/dev/null
  gcloud run services describe "${name}" --region="${REGION}" --format='value(status.url)'
}

echo "==> Building ai-assistance image"
gcloud builds submit ./ai_assistance -t "${REGISTRY}/ai-assistance:latest"
AI_URL="$(deploy_service ai-assistance \
  "${AI_SA}" \
  --image "${REGISTRY}/ai-assistance:latest" \
  --port 8000 --memory 512Mi \
  --set-secrets "GROQ_API_KEY=${SECRET_NAME}:latest")"

echo "==> Building vacation-mode image"
gcloud builds submit ./vacation_mode -t "${REGISTRY}/vacation-mode:latest"
VACATION_URL="$(deploy_service vacation-mode \
  "${VACATION_SA}" \
  --image "${REGISTRY}/vacation-mode:latest" \
  --port 8001 --memory 512Mi \
  --set-env-vars "AI_ASSISTANCE_URL=${AI_URL}")"

echo "==> Building backend image"
gcloud builds submit ./backend -t "${REGISTRY}/backend:latest"
BACKEND_ENV_VARS="DATABASE_URL=${CLOUDSQL_URL},APP_ENV=production,AUTO_SEED=true,SEED_STARTER_PLANTS=false,SESSION_LIFETIME_DAYS=7,CORS_ORIGINS=*,GCP_PROJECT_ID=${PROJECT_ID}"
BACKEND_SECRET_ARGS=()
if [[ "${NOTIFICATIONS_CONFIGURED}" == "true" ]]; then
  BACKEND_ENV_VARS="${BACKEND_ENV_VARS},VAPID_PUBLIC_KEY=${VAPID_PUBLIC_KEY_VALUE},VAPID_SUBJECT=${VAPID_SUBJECT_VALUE},PUBSUB_NOTIFICATION_TOPIC=${PUBSUB_TOPIC},PUBSUB_PUSH_SERVICE_ACCOUNT=${PUBSUB_PUSH_SA},SCHEDULER_SERVICE_ACCOUNT=${SCHEDULER_SA}"
  BACKEND_SECRET_ARGS=(
    --set-secrets "VAPID_PRIVATE_KEY=${VAPID_SECRET_NAME}:latest"
  )
fi
BACKEND_URL="$(deploy_service backend \
  "${BACKEND_SA}" \
  --image "${REGISTRY}/backend:latest" \
  --port 8000 --memory 512Mi \
  --add-cloudsql-instances "${INSTANCE_CONNECTION}" \
  --set-env-vars "${BACKEND_ENV_VARS}" \
  "${BACKEND_SECRET_ARGS[@]}")"

if [[ "${NOTIFICATIONS_CONFIGURED}" == "true" ]]; then
  echo "==> Securing notification callers with Google OIDC"
  gcloud run services update backend \
    --region="${REGION}" \
    --update-env-vars="PUBSUB_PUSH_AUDIENCE=${BACKEND_URL},SCHEDULER_AUDIENCE=${BACKEND_URL}" >/dev/null
  gcloud run services add-iam-policy-binding backend \
    --region="${REGION}" \
    --member="serviceAccount:${PUBSUB_PUSH_SA}" \
    --role="roles/run.invoker" >/dev/null
  gcloud run services add-iam-policy-binding backend \
    --region="${REGION}" \
    --member="serviceAccount:${SCHEDULER_SA}" \
    --role="roles/run.invoker" >/dev/null

  echo "==> Configuring authenticated Pub/Sub push delivery"
  PUBSUB_PUSH_ARGS=(
    --push-endpoint="${BACKEND_URL}/internal/notifications/pubsub"
    --push-auth-service-account="${PUBSUB_PUSH_SA}"
    --push-auth-token-audience="${BACKEND_URL}"
    --ack-deadline=60
    --min-retry-delay=10s
    --max-retry-delay=600s
  )
  if gcloud pubsub subscriptions describe "${PUBSUB_SUBSCRIPTION}" >/dev/null 2>&1; then
    gcloud pubsub subscriptions update "${PUBSUB_SUBSCRIPTION}" "${PUBSUB_PUSH_ARGS[@]}"
  else
    gcloud pubsub subscriptions create "${PUBSUB_SUBSCRIPTION}" \
      --topic="${PUBSUB_TOPIC}" \
      "${PUBSUB_PUSH_ARGS[@]}"
  fi

  echo "==> Scheduling due-care scans every 15 minutes"
  SCHEDULER_ARGS=(
    --location "${REGION}"
    --schedule "*/15 * * * *"
    --uri "${BACKEND_URL}/internal/notifications/dispatch"
    --http-method POST
    --oidc-service-account-email "${SCHEDULER_SA}"
    --oidc-token-audience "${BACKEND_URL}"
  )
  if gcloud scheduler jobs describe plant-guardian-notifications --location "${REGION}" >/dev/null 2>&1; then
    gcloud scheduler jobs update http plant-guardian-notifications "${SCHEDULER_ARGS[@]}"
  else
    gcloud scheduler jobs create http plant-guardian-notifications "${SCHEDULER_ARGS[@]}"
  fi
else
  echo "==> Push notifications are disabled (no VAPID key pair supplied)"
fi

echo "==> Building frontend image (API URLs baked in at build time)"
gcloud builds submit ./frontend --config deploy/cloudbuild-frontend.yaml \
  --substitutions "_API_URL=${BACKEND_URL},_VACATION_API_URL=${VACATION_URL},_GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID_VALUE},_IMAGE=${REGISTRY}/frontend:latest"
FRONTEND_URL="$(deploy_service frontend \
  "${FRONTEND_SA}" \
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
