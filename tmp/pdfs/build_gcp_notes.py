from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output" / "pdf" / "plant-guardian-gcp-connection-guide.pdf"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

GREEN = colors.HexColor("#21603D")
DARK = colors.HexColor("#123B29")
MID = colors.HexColor("#4B9B69")
LIGHT = colors.HexColor("#EAF6ED")
PALE = colors.HexColor("#F5FAF6")
INK = colors.HexColor("#17382A")
MUTED = colors.HexColor("#557265")
LINE = colors.HexColor("#C8DED0")
AMBER = colors.HexColor("#93620A")
RED = colors.HexColor("#A8413E")

s = getSampleStyleSheet()
s.add(ParagraphStyle(name="Kicker", parent=s["Normal"], fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=MID, spaceAfter=10))
s.add(ParagraphStyle(name="CoverTitle", parent=s["Title"], fontName="Helvetica-Bold", fontSize=29, leading=34, textColor=DARK, spaceAfter=12))
s.add(ParagraphStyle(name="CoverSub", parent=s["Normal"], fontName="Helvetica", fontSize=13, leading=19, textColor=MUTED, spaceAfter=18))
s.add(ParagraphStyle(name="H1PG", parent=s["Heading1"], fontName="Helvetica-Bold", fontSize=19, leading=23, textColor=DARK, spaceBefore=5, spaceAfter=10))
s.add(ParagraphStyle(name="H2PG", parent=s["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=GREEN, spaceBefore=12, spaceAfter=6))
s.add(ParagraphStyle(name="BodyPG", parent=s["BodyText"], fontName="Helvetica", fontSize=9.3, leading=14, textColor=INK, spaceAfter=7))
s.add(ParagraphStyle(name="SmallPG", parent=s["BodyText"], fontName="Helvetica", fontSize=8, leading=11, textColor=MUTED, spaceAfter=4))
s.add(ParagraphStyle(name="BulletPG", parent=s["BodyText"], fontName="Helvetica", fontSize=9.1, leading=13.2, textColor=INK, leftIndent=13, firstLineIndent=-8, spaceAfter=4))
s.add(ParagraphStyle(name="HeadPG", parent=s["BodyText"], fontName="Helvetica-Bold", fontSize=8, leading=10.5, textColor=colors.white))
s.add(ParagraphStyle(name="CellPG", parent=s["BodyText"], fontName="Helvetica", fontSize=7.6, leading=10.2, textColor=INK))
s.add(ParagraphStyle(name="CodePG", parent=s["Code"], fontName="Courier", fontSize=7, leading=9, textColor=DARK, backColor=PALE, borderColor=LINE, borderWidth=0.5, borderPadding=7, spaceBefore=3, spaceAfter=8))
s.add(ParagraphStyle(name="CalloutPG", parent=s["BodyText"], fontName="Helvetica", fontSize=8.9, leading=13, textColor=INK, backColor=LIGHT, borderColor=LINE, borderWidth=0.6, borderPadding=9, spaceBefore=5, spaceAfter=8))


def para(text, style="BodyPG"):
    return Paragraph(escape(text).replace("\n", "<br/>"), s[style])


def code(text):
    return Preformatted(text.strip("\n"), s["CodePG"])


def bullets(items):
    return [para("- " + item, "BulletPG") for item in items]


def heading(title):
    return [Spacer(1, 3), Paragraph(escape(title), s["H1PG"]), HRFlowable(width="100%", thickness=0.7, color=LINE, spaceAfter=10)]


def sub(title):
    return Paragraph(escape(title), s["H2PG"])


def make_table(headers, rows, widths, header_color=GREEN):
    data = [[Paragraph(escape(str(x)), s["HeadPG"]) for x in headers]]
    data.extend([[Paragraph(escape(str(x)), s["CellPG"]) for x in row] for row in rows])
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def callout(label, text, color=GREEN):
    content = [Paragraph(escape(label), ParagraphStyle("CalloutLabel", parent=s["SmallPG"], fontName="Helvetica-Bold", textColor=color, spaceAfter=3)), para(text, "CalloutPG")]
    t = Table([[content]], colWidths=[174 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def link(label, url):
    return Paragraph(f'<link href="{url}" color="#21603D"><u>{escape(label)}</u></link>', s["SmallPG"])


def page_header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, height - 14 * mm, width - doc.rightMargin, height - 14 * mm)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(GREEN)
    canvas.drawString(doc.leftMargin, height - 10 * mm, "PLANT GUARDIAN")
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(width - doc.rightMargin, height - 10 * mm, "GCP connection and operations guide")
    canvas.line(doc.leftMargin, 13 * mm, width - doc.rightMargin, 13 * mm)
    canvas.drawCentredString(width / 2, 8 * mm, f"Plant Guardian | Page {doc.page}")
    canvas.restoreState()


story = [
    Spacer(1, 27 * mm),
    Paragraph("PLANT GUARDIAN", s["Kicker"]),
    Paragraph("GCP Connection and\nOperations Guide", s["CoverTitle"]),
    Paragraph("A consolidated technical note explaining how Plant Guardian uses Google Cloud Platform, how requests and data flow through the system, where each resource is managed, and how to operate the deployment safely.", s["CoverSub"]),
    Spacer(1, 8 * mm),
    make_table(["Project", "Value"], [
        ["GCP project", "gcp-hackathon-506604"],
        ["Primary region", "asia-south1 (Mumbai)"],
        ["Application", "Plant Guardian full-stack plant care dashboard"],
        ["Cloud scope", "Cloud Run, Cloud SQL, Artifact Registry, Cloud Build, Secret Manager, IAM, Scheduler, Pub/Sub, and Google OAuth"],
    ], [38 * mm, 136 * mm]),
    Spacer(1, 15 * mm),
    callout("Product message", "Most trackers tell you good or bad. Plant Guardian tells you how urgent."),
    Spacer(1, 35 * mm),
    para("Prepared from the Plant Guardian repository, deployment configuration, and deployed service details supplied for this project.", "SmallPG"),
    PageBreak(),
]

story += heading("1. Executive summary")
story += [
    para("Plant Guardian is deployed as a compact, stateless service platform on Google Cloud. The browser reaches a Next.js frontend on Cloud Run. The frontend uses same-origin /api rewrites to reach the FastAPI backend and Vacation Mode service. The backend owns authentication, plant CRUD, risk calculations, watering history, gamification, pet-safety metadata, and notification orchestration. PostgreSQL data lives in Cloud SQL."),
    para("AI text generation is isolated in a separate ai-assistance Cloud Run service. It receives the Groq API key from Secret Manager and is called by vacation-mode through an internal service URL. The design separates UI, API, database, messaging, and AI responsibilities while keeping deployment simple."),
    callout("Current state", "The deployed architecture contains four Cloud Run services, one managed PostgreSQL instance, one regional Artifact Registry repository, Cloud Build image delivery, Secret Manager secrets, six dedicated service accounts, a Cloud Scheduler job, and conditional Pub/Sub notification delivery."),
    sub("Quick navigation map"),
    make_table(["Need to do", "Console location", "Resource"], [
        ["Open live app services", "Cloud Run > Services", "frontend, backend, vacation-mode, ai-assistance"],
        ["Inspect database", "SQL > Instances", "plant-guardian-db"],
        ["Inspect Docker images", "Artifact Registry > Repositories", "plant-guardian"],
        ["Review builds", "Cloud Build > History", "frontend/backend builds"],
        ["Manage secrets", "Security > Secret Manager", "groq-api-key, optional VAPID secret"],
        ["Review identities", "IAM & Admin > Service Accounts / IAM", "six Plant Guardian accounts"],
        ["Inspect schedule", "Cloud Scheduler > Jobs", "plant-guardian-notifications"],
        ["Inspect events", "Pub/Sub > Topics / Subscriptions", "plant-care-notifications"],
        ["Manage Google login", "Google Auth Platform > Clients", "Plant Guardian Web client"],
    ], [46 * mm, 74 * mm, 54 * mm]),
]

story += heading("2. Architecture and request flow")
story += [
    sub("High-level topology"),
    code("""Browser
  |
  v
frontend (Next.js on Cloud Run)
  |-- /api/plants, /api/auth, /api/profile, /api/notifications
  |       -> backend (FastAPI on Cloud Run)
  |              |-> Cloud SQL PostgreSQL through Cloud SQL socket
  |              |-> Pub/Sub publisher for asynchronous reminders
  |              |-> browser Web Push when reminders are enabled
  |
  |-- /api/vacation-mode
          -> vacation-mode (FastAPI on Cloud Run)
                 -> ai-assistance (FastAPI on Cloud Run)
                        -> Groq API using Secret Manager key

Cloud Scheduler (OIDC identity)
  -> backend /internal/notifications/dispatch
       -> Pub/Sub topic -> authenticated push subscription
            -> backend /internal/notifications/pubsub -> browser Web Push
"""),
    para("The browser usually sees only the frontend URL. Next.js rewrites keep backend and Vacation Mode URLs server-side. This avoids exposing internal topology in normal browser links and gives the deployment a clean frontend gateway."),
    sub("Resource identifiers"),
    make_table(["Identifier", "Value", "Purpose"], [
        ["Project", "gcp-hackathon-506604", "Resource, IAM, API, billing, and log boundary."],
        ["Region", "asia-south1", "Primary location for compute and data resources."],
        ["Registry", "asia-south1-docker.pkg.dev/gcp-hackathon-506604/plant-guardian", "Private image repository."],
        ["SQL instance", "plant-guardian-db", "Managed PostgreSQL host."],
        ["SQL database", "plant_guardian", "Application database."],
    ], [38 * mm, 70 * mm, 66 * mm]),
]

story += heading("3. GCP services and their role")
story += [
    sub("3.1 Cloud Run: application hosting"),
    para("Cloud Run runs each Docker container as a managed HTTPS service. It creates revisions for deployments, routes traffic, autos-scales instances, emits logs and metrics, and can scale idle services to zero. Plant Guardian uses four services so the dashboard, core API, vacation planner, and AI adapter remain independently deployable."),
    make_table(["Service", "What it does", "URL"], [
        ["frontend", "Next.js dashboard, auth UI, plant cards, profile, reminders, and API proxy.", "https://frontend-845145311784.asia-south1.run.app"],
        ["backend", "FastAPI API, sessions, plant logic, PostgreSQL, notifications, and business rules.", "https://backend-845145311784.asia-south1.run.app"],
        ["vacation-mode", "Creates vacation watering plans and caretaker briefings.", "https://vacation-mode-845145311784.asia-south1.run.app"],
        ["ai-assistance", "Calls Groq for care and vacation wording.", "https://ai-assistance-845145311784.asia-south1.run.app"],
    ], [28 * mm, 92 * mm, 54 * mm]),
    sub("How to access"),
    para("Console path: Cloud Run > Services > select a service. The service page exposes the URL, revisions, logs, metrics, environment configuration, scaling settings, and traffic split."),
    code("""gcloud run services list --project gcp-hackathon-506604 --region asia-south1
gcloud run services describe backend --project gcp-hackathon-506604 --region asia-south1
gcloud run services logs read backend --project gcp-hackathon-506604 --region asia-south1 --limit 50
"""),
    sub("3.2 Cloud SQL: durable PostgreSQL"),
    para("Cloud SQL is the production persistence layer. It stores users, sessions, plants, watering rows, care events, notification subscriptions, and application metadata. Risk scores, seasonal frequency, mood, and other care metrics are calculated at response time rather than stored as stale values."),
    para("The backend uses a Cloud SQL Unix socket. Its production connection string follows this shape:"),
    code("postgresql+psycopg://USER:PASSWORD@/plant_guardian?host=/cloudsql/PROJECT:REGION:INSTANCE"),
    para("Cloud Run attaches the SQL instance with --add-cloudsql-instances and the backend service account receives roles/cloudsql.client. The backend startup entrypoint runs Alembic migrations before launching FastAPI."),
    para("Console path: SQL > Instances > plant-guardian-db. Use the overview, connections, databases, users, backups, operations, logs, maintenance, and Query Insights pages."),
    code("""gcloud sql instances describe plant-guardian-db --project gcp-hackathon-506604
gcloud sql databases list --instance plant-guardian-db --project gcp-hackathon-506604
gcloud sql users list --instance plant-guardian-db --project gcp-hackathon-506604
"""),
    callout("Database protection", "Do not delete the Cloud SQL instance or its production data without a backup and an explicit recovery plan. The current deployment script passes the database password through deployment configuration; moving it to Secret Manager is a recommended hardening task.", RED),
    sub("3.3 Artifact Registry: private image storage"),
    para("Artifact Registry stores the Docker images executed by Cloud Run. Cloud Build pushes images such as backend:latest and frontend:latest to the regional plant-guardian repository. IAM controls who can push, pull, or delete images."),
    para("Console path: Artifact Registry > Repositories > plant-guardian. Review packages, tags, digests, image size, vulnerability findings when enabled, and cleanup policies."),
    code("""gcloud artifacts repositories list --location asia-south1 --project gcp-hackathon-506604
gcloud artifacts docker images list asia-south1-docker.pkg.dev/gcp-hackathon-506604/plant-guardian --include-tags
"""),
    sub("3.4 Cloud Build: reproducible builds"),
    para("Cloud Build builds the Docker image outside the developer laptop. The submitted source directory is archived, Dockerfile steps run in a managed build worker, and the output image is pushed to Artifact Registry. This makes production builds repeatable."),
    para("The frontend build file deploy/cloudbuild-frontend.yaml passes API_URL and VACATION_API_URL for Next.js rewrites. It also passes NEXT_PUBLIC_GOOGLE_CLIENT_ID because that public value is embedded during the Next.js production build."),
    para("Console path: Cloud Build > History. Select a build to view substitutions, steps, logs, duration, source, and output image."),
    code("""gcloud builds list --project gcp-hackathon-506604 --limit 20
gcloud builds log BUILD_ID --project gcp-hackathon-506604
"""),
    callout("Build-time behavior", "The first build can be slow because it downloads base images and dependencies. For a normal change, submit only .\\backend or .\\frontend instead of archiving the entire monorepo.", AMBER),
]

story += heading("4. Secrets, identities, and security")
story += [
    sub("4.1 Secret Manager"),
    para("Secret Manager keeps sensitive values out of source code and image layers. The deployment stores the Groq API key as groq-api-key and injects it into ai-assistance as GROQ_API_KEY. If browser push reminders are enabled, the VAPID private key is stored as plant-guardian-vapid-private-key and injected into backend."),
    para("The Google Web OAuth client ID is public configuration, not a secret. It belongs in the frontend build argument and backend audience configuration, but a Google client secret must never be placed in a NEXT_PUBLIC_* variable."),
    para("Console path: Security > Secret Manager > select a secret. Review versions, replication, IAM, and rotation history. Do not print payload values into logs."),
    code("""gcloud secrets list --project gcp-hackathon-506604
gcloud secrets versions list groq-api-key --project gcp-hackathon-506604
"""),
    sub("4.2 IAM and service accounts"),
    para("Dedicated service identities reduce blast radius. The deployment creates six accounts and attaches only the permissions needed by each runtime."),
    make_table(["Identity", "Attached to", "Access"], [
        ["plant-guardian-frontend", "frontend Cloud Run", "No project data role; serves the web app."],
        ["plant-guardian-backend", "backend Cloud Run", "Cloud SQL Client, Pub/Sub publisher, optional VAPID accessor."],
        ["plant-guardian-vacation", "vacation-mode Cloud Run", "Service runtime; calls AI Assistance."],
        ["plant-guardian-ai", "ai-assistance Cloud Run", "Groq secret accessor only."],
        ["plant-guardian-scheduler", "Cloud Scheduler OIDC", "Cloud Run Invoker on backend dispatch."],
        ["plant-guardian-pubsub-push", "Pub/Sub push OIDC", "Cloud Run Invoker on backend worker."],
    ], [52 * mm, 39 * mm, 83 * mm]),
    para("The deployer receives Service Account User on these identities so it can attach them to Cloud Run. The Pub/Sub service agent receives Service Account Token Creator only on the push identity so it can mint an authenticated push token."),
    para("Console path: IAM & Admin > Service Accounts for account-level inspection, and IAM & Admin > IAM for project bindings. Prefer managed identities over downloaded service-account keys."),
    code("""gcloud iam service-accounts list --project gcp-hackathon-506604
gcloud projects get-iam-policy gcp-hackathon-506604
"""),
]

story += heading("5. Notifications: Scheduler and Pub/Sub")
story += [
    sub("5.1 Cloud Scheduler"),
    para("Cloud Scheduler is the time-based trigger. The job plant-guardian-notifications runs every 15 minutes in UTC and sends POST /internal/notifications/dispatch. It uses an OIDC token minted for plant-guardian-scheduler. The backend verifies the token audience and caller identity before scanning due or overdue plants."),
    para("Console path: Cloud Scheduler > Jobs > plant-guardian-notifications. Inspect the schedule, time zone, target URI, OIDC service account, retry policy, last run, and response status. Run now is useful for controlled tests."),
    code("""gcloud scheduler jobs describe plant-guardian-notifications \\
  --location asia-south1 --project gcp-hackathon-506604
gcloud scheduler jobs run plant-guardian-notifications \\
  --location asia-south1 --project gcp-hackathon-506604
"""),
    sub("5.2 Pub/Sub"),
    para("Pub/Sub is the asynchronous transport. The backend publishes a compact delivery event to plant-care-notifications. The push subscription plant-care-notifications-push calls POST /internal/notifications/pubsub using a Google-signed OIDC token for plant-guardian-pubsub-push. The backend loads plant and browser subscription context from PostgreSQL and performs Web Push delivery."),
    para("Pub/Sub provides retry and decoupling. Idempotent delivery records prevent duplicate notifications when Scheduler scans or Pub/Sub pushes are retried. The topic and subscription are created only when both VAPID public and private keys are provided."),
    para("Console path: Pub/Sub > Topics > plant-care-notifications, then Pub/Sub > Subscriptions > plant-care-notifications-push. Review push endpoint, authentication identity, retention, retries, and delivery metrics."),
    code("""gcloud pubsub topics describe plant-care-notifications --project gcp-hackathon-506604
gcloud pubsub subscriptions describe plant-care-notifications-push --project gcp-hackathon-506604
"""),
    callout("Status", "Pub/Sub is implemented in the repository and deployment script. It is active only when VAPID notification configuration is enabled. If VAPID keys are absent, the rest of Plant Guardian still deploys and the direct/local notification path remains available.", AMBER),
]

story += heading("6. Google login and OAuth")
story += [
    para("Google Sign-In is managed through Google Auth Platform, separate from Cloud Run. The frontend loads Google Identity Services and receives an ID-token credential. The backend validates the token audience against GOOGLE_CLIENT_ID, then starts or creates the Plant Guardian session."),
    para("New Google users must complete name, place, and pets before account creation. Existing users can sign in with Google once their email is associated with an account."),
    sub("Configuration"),
    *bullets(["Create a Web application OAuth client in Google Auth Platform.", "Register http://localhost:3000 and each deployed frontend origin as Authorized JavaScript origins.", "Use External audience for users outside your organization; while in Testing, add testers under Audience > Test users.", "Keep default openid, email, and profile scopes; no extra Google API scopes are required.", "No redirect URI is needed for the JavaScript callback flow used by this project."]),
    sub("Connection to the deployment"),
    make_table(["Variable", "Where it goes", "Why"], [
        ["GOOGLE_CLIENT_ID", "Backend Cloud Run environment", "Audience used to verify Google ID tokens."],
        ["NEXT_PUBLIC_GOOGLE_CLIENT_ID", "Frontend Cloud Build argument", "Public browser client ID embedded in Next.js."],
    ], [57 * mm, 58 * mm, 59 * mm]),
    code("""gcloud run services update backend \\
  --region asia-south1 \\
  --update-env-vars=GOOGLE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
"""),
    callout("Important", "Updating only the backend is not enough. NEXT_PUBLIC_GOOGLE_CLIENT_ID is read during the frontend production build, so changing it requires a new frontend image build and Cloud Run frontend deployment.", RED),
]

story += heading("7. Deployment and change workflow")
story += [
    sub("Full deployment"),
    para("deploy/gcp-deploy.sh enables APIs, creates or reuses infrastructure, configures IAM, builds four images, deploys services in dependency order, and optionally creates Pub/Sub and Scheduler resources. It is appropriate for initial setup or a coordinated infrastructure refresh."),
    code("""# Bash / Git Bash
export GCP_PROJECT_ID=gcp-hackathon-506604
export GCP_REGION=asia-south1
export GROQ_API_KEY=YOUR_NEW_KEY
bash deploy/gcp-deploy.sh
"""),
    para("On Windows CMD use set VAR=value. On PowerShell use $env:VAR = value. Do not use export in CMD or PowerShell, and do not add backslashes before underscores."),
    sub("Single-service redeploy"),
    para("For ordinary code changes, build and deploy only the changed service. This is faster and avoids touching unchanged AI, Vacation Mode, database, Scheduler, or Pub/Sub resources."),
    code("""# Backend
gcloud builds submit .\\backend --project=%PROJECT_ID% --tag=%BACKEND_IMAGE%
gcloud run deploy backend --project=%PROJECT_ID% --region=%REGION% \\
  --image=%BACKEND_IMAGE% \\
  --service-account=plant-guardian-backend@%PROJECT_ID%.iam.gserviceaccount.com

# Frontend
gcloud builds submit .\\frontend --project=%PROJECT_ID% \\
  --config=deploy\\cloudbuild-frontend.yaml \\
  --substitutions="_API_URL=%BACKEND_URL%,_VACATION_API_URL=%VACATION_URL%,_GOOGLE_CLIENT_ID=%GOOGLE_CLIENT_ID%,_IMAGE=%FRONTEND_IMAGE%"
gcloud run deploy frontend --project=%PROJECT_ID% --region=%REGION% \\
  --image=%FRONTEND_IMAGE% --allow-unauthenticated
"""),
    sub("Revision and rollback"),
    para("Every Cloud Run deploy creates a revision. In Cloud Run > service > Revisions, route traffic to a known-good revision if a deployment fails. Keep the previous revision until smoke tests pass."),
    code("""gcloud run services update-traffic backend \\
  --region asia-south1 \\
  --to-revisions=backend-00002-ABC=100
"""),
]

story += heading("8. Operations, cost, and security")
story += [
    sub("Daily checks"),
    *bullets(["Cloud Run: review startup logs, error rates, latency, instance count, and revision traffic.", "Cloud SQL: confirm backups, storage headroom, connection health, and migration success.", "Cloud Build: retain successful build IDs and inspect failed step logs.", "Scheduler: inspect the last response and use Run now only for controlled tests.", "Pub/Sub: watch undelivered messages, retry counts, and push response codes.", "Secret Manager and IAM: review access bindings and rotate secrets deliberately."]),
    sub("Cost model"),
    make_table(["Resource", "Main cost driver", "Practical control"], [
        ["Cloud Run", "Request compute and running instances.", "Tune memory, concurrency, max instances; allow scale-to-zero."],
        ["Cloud SQL", "Provisioned instance, storage, backups, network.", "Choose the right tier and backup retention."],
        ["Cloud Build", "Build minutes and artifact storage.", "Build only changed services; reuse layers."],
        ["Artifact Registry", "Stored image layers and retrieval.", "Clean old untagged images."],
        ["Scheduler / Pub/Sub", "Job executions, messages, retention.", "Keep one bounded 15-minute workflow."],
    ], [35 * mm, 75 * mm, 64 * mm]),
    sub("Security checklist"),
    *bullets(["Rotate any API key exposed in a terminal transcript, chat, screenshot, or repository.", "Never commit .env, database passwords, Groq keys, VAPID private keys, or service-account keys.", "Use the dedicated service accounts and OIDC callers created by the deployment.", "Restrict CORS_ORIGINS to deployed frontend origins in a hardened production setup.", "Keep notification routes protected; do not make internal endpoints public just to test them.", "Use Cloud SQL backups and verify restore procedures before a production release.", "Use OAuth Testing users until the Google app is ready for its intended audience."]),
    callout("Recommended hardening", "Move the Cloud SQL password from deployment environment configuration into Secret Manager and inject it into the backend. This is the main security improvement still visible in the current deployment pattern.", AMBER),
]

story += heading("9. Verification checklist and references")
story.append(make_table(["Check", "Expected result"], [
    ["Cloud Run", "Four services are healthy and the intended revisions receive traffic."],
    ["Frontend", "Dashboard opens, API proxy works, and Google button is interactive."],
    ["Backend", "GET /health reports database-aware health; CRUD and watering work."],
    ["Database", "Alembic schema is current and backups are configured."],
    ["Google OAuth", "Authorized origins and test users are correct; client ID matches backend and frontend."],
    ["Scheduler", "15-minute job exists with OIDC and a successful last response."],
    ["Pub/Sub", "Topic and authenticated push subscription exist when VAPID mode is enabled."],
    ["Rollback", "Previous healthy frontend and backend revisions remain available."],
], [54 * mm, 120 * mm]))
story.append(sub("Smoke-test commands"))
story.append(code("""gcloud run services list --project gcp-hackathon-506604 --region asia-south1
curl https://backend-845145311784.asia-south1.run.app/health
gcloud scheduler jobs run plant-guardian-notifications --location asia-south1 --project gcp-hackathon-506604
"""))
story.append(sub("Project references"))
for item in ["README.md - overview, environment variables, APIs, local setup, and deployment summary.", "DEPLOY_GCP.md - architecture, IAM matrix, Pub/Sub flow, redeploy, teardown, and cost notes.", "deploy/gcp-deploy.sh - automated GCP resource setup and service deployment.", "deploy/cloudbuild-frontend.yaml - frontend build arguments and image output.", ".env.example and docker-compose.yml - local configuration and service topology."]:
    story.append(para("- " + item, "BulletPG"))
story.append(para("Official documentation:", "SmallPG"))
for label, url in [("Cloud Run", "https://cloud.google.com/run/docs"), ("Cloud SQL", "https://cloud.google.com/sql/docs"), ("Artifact Registry", "https://cloud.google.com/artifact-registry/docs"), ("Cloud Build", "https://cloud.google.com/build/docs"), ("Secret Manager", "https://cloud.google.com/secret-manager/docs"), ("IAM service accounts", "https://cloud.google.com/iam/docs/service-account-overview"), ("Cloud Scheduler", "https://cloud.google.com/scheduler/docs"), ("Pub/Sub", "https://cloud.google.com/pubsub/docs"), ("Google Identity Services", "https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid")]:
    story.append(link(label, url))
story.append(Spacer(1, 6))
story.append(callout("Final architecture statement", "Plant Guardian uses GCP as a managed runtime and integration layer: Cloud Run hosts stateless services, Cloud SQL stores durable state, Artifact Registry and Cloud Build deliver containers, Secret Manager protects runtime secrets, IAM limits access, Scheduler supplies time-based triggers, Pub/Sub supplies durable asynchronous delivery, and Google Auth Platform supplies optional Google account authentication."))
story += heading("10. Troubleshooting quick reference")
story.append(make_table(["Symptom", "First checks", "Likely fix"], [
    ["Cloud Run deploy fails", "Cloud Build History and the failed step log.", "Fix the image build or environment value, then redeploy the affected service only."],
    ["Frontend cannot reach API", "Cloud Run frontend logs, API_URL, and Next.js rewrite target.", "Confirm the backend URL is HTTPS and that the new frontend revision received traffic."],
    ["Database connection error", "Cloud Run backend logs, Cloud SQL instance state, and --add-cloudsql-instances attachment.", "Restore the attachment, verify DATABASE_URL format, and check IAM Cloud SQL Client access."],
    ["Google button does nothing", "Browser console, frontend build variable, OAuth client origins, and test-user list.", "Rebuild frontend with NEXT_PUBLIC_GOOGLE_CLIENT_ID and add the exact deployed origin."],
    ["Reminder not delivered", "Scheduler last response, Pub/Sub undelivered messages, and VAPID configuration.", "Run the Scheduler job manually, inspect push response codes, and verify the authenticated push identity."],
    ["Need to undo a release", "Cloud Run Revisions and traffic percentages.", "Route 100 percent of traffic to the last known-good revision, then investigate the failed one."],
], [42 * mm, 66 * mm, 66 * mm]))
story.append(callout("Safe operating rule", "When diagnosing production, prefer read-only inspection first: logs, revisions, metrics, IAM policy, Scheduler history, and Pub/Sub delivery status. Change one service or one configuration value at a time, record the revision, and keep a known-good rollback target."))

doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=20 * mm, bottomMargin=18 * mm, title="Plant Guardian GCP Connection and Operations Guide", author="Plant Guardian", subject="GCP architecture, access, operations, and deployment notes")
doc.build(story, onFirstPage=page_header_footer, onLaterPages=page_header_footer)
print(OUTPUT)
