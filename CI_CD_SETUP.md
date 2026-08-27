# Plant Guardian CI/CD

Plant Guardian uses two Google Cloud Build pipelines:

- `cloudbuild-ci.yaml`: runs backend tests plus frontend tests, lint, and production build for pull requests targeting `main`.
- `deploy/cloudbuild-python-service.yaml`: tests, builds, and deploys only the Python service whose directory changed.
- `deploy/cloudbuild-frontend-deploy.yaml`: tests, builds, and deploys the frontend only when frontend files change.
- `cloudbuild.yaml`: an optional full-release pipeline for intentionally rebuilding all four services.

The deployment pipeline updates only container images. It does not recreate or delete Cloud SQL, Secret Manager values, Scheduler jobs, Pub/Sub resources, IAM runtime accounts, or application data.

## One-time setup

1. Push these CI/CD files to the GitHub repository.
2. Open Google Cloud Console, select `gcp-hackathon-506604`, and navigate to **Cloud Build > Triggers**.
3. Click **Connect repository**, choose GitHub, authorize Google Cloud Build, and connect `joelsamgit/Cognizant-hackathon`.
4. Ensure `.env` contains `GCP_PROJECT_ID`, `GCP_REGION`, and the Google OAuth client ID.
5. From Git Bash in the project directory, run:

```bash
bash deploy/setup-cicd.sh
```

The script creates a dedicated `plant-guardian-cicd` service account, assigns its build and deploy roles, and creates one pull-request check plus four path-filtered deployment triggers. This avoids rebuilding unchanged services.

## Daily workflow

Create a branch and push it:

```bash
git switch -c feature/my-change
git add .
git commit -m "Describe the change"
git push -u origin feature/my-change
```

Open a pull request into `main`. The `plant-guardian-pr-checks` trigger validates the project without deploying it. After the pull request is merged, only the triggers whose service directories changed build and deploy their commits automatically.

## Monitor builds

Open **Google Cloud Console > Cloud Build > History**. Select a build to see each test, image build, push, and Cloud Run deployment step.

To inspect the triggers from the CLI:

```bash
gcloud builds triggers list --region=asia-south1
```

To inspect deployed revisions:

```bash
gcloud run services list --region=asia-south1
```

## Required behavior

- A failed test, lint check, frontend build, Docker build, image push, or Cloud Run update stops the pipeline.
- Pull requests never deploy.
- Only commits merged into `main` deploy automatically.
- Existing Cloud Run environment variables, Cloud SQL connections, secrets, service accounts, and IAM settings are preserved because the pipeline only updates each service image.
