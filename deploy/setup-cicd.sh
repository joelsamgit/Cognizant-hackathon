#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-asia-south1}"
GITHUB_OWNER="${GITHUB_OWNER:-joelsamgit}"
GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-Cognizant-hackathon}"
CICD_SERVICE_ACCOUNT_NAME="plant-guardian-cicd"
CICD_SERVICE_ACCOUNT="${CICD_SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
GOOGLE_CLIENT_ID_VALUE="${NEXT_PUBLIC_GOOGLE_CLIENT_ID:-${GOOGLE_CLIENT_ID:-}}"

if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
  echo "Set GCP_PROJECT_ID or select a gcloud project first." >&2
  exit 1
fi

gcloud config set project "${PROJECT_ID}"
gcloud services enable cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com iam.googleapis.com

if ! gcloud iam service-accounts describe "${CICD_SERVICE_ACCOUNT}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${CICD_SERVICE_ACCOUNT_NAME}" \
    --display-name="Plant Guardian CI/CD"
fi

for role in \
  roles/cloudbuild.builds.builder \
  roles/run.admin \
  roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${CICD_SERVICE_ACCOUNT}" \
    --role="${role}" >/dev/null
done

create_trigger() {
  local name="$1"
  shift
  if gcloud builds triggers describe "${name}" --region="${REGION}" >/dev/null 2>&1; then
    echo "${name} already exists"
    return
  fi
  gcloud builds triggers create github \
    --name="${name}" \
    --region="${REGION}" \
    --repo-owner="${GITHUB_OWNER}" \
    --repo-name="${GITHUB_REPOSITORY}" \
    --service-account="projects/${PROJECT_ID}/serviceAccounts/${CICD_SERVICE_ACCOUNT}" \
    "$@"
}

create_trigger plant-guardian-pr-checks \
  --pull-request-pattern="^main$" \
  --build-config="cloudbuild-ci.yaml" \
  --comment-control="COMMENTS_DISABLED"

create_trigger plant-guardian-backend-deploy \
  --branch-pattern="^main$" \
  --build-config="deploy/cloudbuild-python-service.yaml" \
  --included-files="backend/**,deploy/cloudbuild-python-service.yaml" \
  --substitutions="_REGION=${REGION},_REPOSITORY=plant-guardian,_SERVICE=backend,_CONTEXT=backend"

create_trigger plant-guardian-ai-deploy \
  --branch-pattern="^main$" \
  --build-config="deploy/cloudbuild-python-service.yaml" \
  --included-files="ai_assistance/**,deploy/cloudbuild-python-service.yaml" \
  --substitutions="_REGION=${REGION},_REPOSITORY=plant-guardian,_SERVICE=ai-assistance,_CONTEXT=ai_assistance"

create_trigger plant-guardian-vacation-deploy \
  --branch-pattern="^main$" \
  --build-config="deploy/cloudbuild-python-service.yaml" \
  --included-files="vacation_mode/**,deploy/cloudbuild-python-service.yaml" \
  --substitutions="_REGION=${REGION},_REPOSITORY=plant-guardian,_SERVICE=vacation-mode,_CONTEXT=vacation_mode"

create_trigger plant-guardian-frontend-deploy \
  --branch-pattern="^main$" \
  --build-config="deploy/cloudbuild-frontend-deploy.yaml" \
  --included-files="frontend/**,deploy/cloudbuild-frontend-deploy.yaml" \
  --substitutions="_REGION=${REGION},_REPOSITORY=plant-guardian,_BACKEND_URL=https://backend-845145311784.${REGION}.run.app,_VACATION_API_URL=https://vacation-mode-845145311784.${REGION}.run.app,_GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID_VALUE}"

echo "Path-filtered CI/CD triggers are configured for ${GITHUB_OWNER}/${GITHUB_REPOSITORY}."
