#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/../.."

script="deploy/setup-cicd.sh"

grep -Fq 'TRIGGER_REGION="${GCP_TRIGGER_REGION:-global}"' "${script}"
grep -Fq 'gcloud builds triggers describe "${name}" --region="${TRIGGER_REGION}"' "${script}"
grep -Fq -- '--region="${TRIGGER_REGION}"' "${script}"
grep -Fq '_REGION=${REGION}' "${script}"
