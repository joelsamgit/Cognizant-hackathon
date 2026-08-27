from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output" / "pdf" / "plant-guardian-technology-and-gcp-study-guide.pdf"
ARCHITECTURE_IMAGE = ROOT / "output" / "architecture" / "plant-guardian-gcp-architecture.png"
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

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="KickerPG", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=MID, spaceAfter=10))
styles.add(ParagraphStyle(name="CoverTitlePG", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=27, leading=32, textColor=DARK, spaceAfter=13))
styles.add(ParagraphStyle(name="CoverSubPG", parent=styles["Normal"], fontName="Helvetica", fontSize=12.5, leading=18, textColor=MUTED, spaceAfter=18))
styles.add(ParagraphStyle(name="H1PG", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=DARK, spaceBefore=5, spaceAfter=8))
styles.add(ParagraphStyle(name="H2PG", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12.5, leading=16, textColor=GREEN, spaceBefore=10, spaceAfter=5))
styles.add(ParagraphStyle(name="BodyPG", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.1, leading=13.5, textColor=INK, spaceAfter=6))
styles.add(ParagraphStyle(name="SmallPG", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.7, leading=10.5, textColor=MUTED, spaceAfter=4))
styles.add(ParagraphStyle(name="BulletPG", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.9, leading=12.8, textColor=INK, leftIndent=13, firstLineIndent=-8, spaceAfter=3))
styles.add(ParagraphStyle(name="HeadPG", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=7.8, leading=10, textColor=colors.white))
styles.add(ParagraphStyle(name="CellPG", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.25, leading=9.7, textColor=INK))
styles.add(ParagraphStyle(name="CodePG", parent=styles["Code"], fontName="Courier", fontSize=7.1, leading=9.2, textColor=DARK, backColor=PALE, borderColor=LINE, borderWidth=0.5, borderPadding=7, spaceBefore=3, spaceAfter=8))
styles.add(ParagraphStyle(name="CalloutLabelPG", parent=styles["SmallPG"], fontName="Helvetica-Bold", textColor=GREEN, spaceAfter=3))
styles.add(ParagraphStyle(name="QuotePG", parent=styles["BodyPG"], fontName="Helvetica-Oblique", fontSize=10.5, leading=16, textColor=DARK, leftIndent=12, rightIndent=12, spaceBefore=7, spaceAfter=7))


def para(value, style="BodyPG"):
    return Paragraph(escape(value).replace("\n", "<br/>"), styles[style])


def code(value):
    return Preformatted(value.strip("\n"), styles["CodePG"])


def bullets(values):
    return [para("- " + value, "BulletPG") for value in values]


def heading(value):
    return [Spacer(1, 3), Paragraph(escape(value), styles["H1PG"]), HRFlowable(width="100%", thickness=0.7, color=LINE, spaceAfter=9)]


def sub(value):
    return Paragraph(escape(value), styles["H2PG"])


def table(headers, rows, widths, header_color=GREEN):
    data = [[Paragraph(escape(str(cell)), styles["HeadPG"]) for cell in headers]]
    data.extend([[Paragraph(escape(str(cell)), styles["CellPG"]) for cell in row] for row in rows])
    result = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return result


def callout(label, value, label_color=GREEN):
    content = [
        Paragraph(escape(label), ParagraphStyle("DynamicCalloutLabel", parent=styles["CalloutLabelPG"], textColor=label_color)),
        para(value, "BodyPG"),
    ]
    result = Table([[content]], colWidths=[174 * mm])
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return result


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
    canvas.drawRightString(width - doc.rightMargin, height - 10 * mm, "Technology and GCP study guide")
    canvas.line(doc.leftMargin, 13 * mm, width - doc.rightMargin, 13 * mm)
    canvas.drawCentredString(width / 2, 8 * mm, f"Plant Guardian | Page {doc.page}")
    canvas.restoreState()


story = [
    Spacer(1, 25 * mm),
    Paragraph("PLANT GUARDIAN", styles["KickerPG"]),
    Paragraph("Technology Stack and<br/>Google Cloud Study Guide", styles["CoverTitlePG"]),
    Paragraph("A detailed learning guide connecting every major Plant Guardian feature to the frontend, backend, database, service, and Google Cloud technology that makes it work.", styles["CoverSubPG"]),
    Spacer(1, 7 * mm),
    table(["Item", "Value"], [
        ["GCP project", "gcp-hackathon-506604"],
        ["Primary region", "asia-south1 (Mumbai)"],
        ["Production frontend", "frontend Cloud Run service"],
        ["Current frontend revision", "frontend-00005-5d8"],
        ["Core stack", "Next.js, React, TypeScript, FastAPI, SQLAlchemy, PostgreSQL"],
    ], [46 * mm, 128 * mm]),
    Spacer(1, 14 * mm),
    callout("Core product idea", "Most trackers tell you good or bad. Plant Guardian tells you how urgent."),
    Spacer(1, 25 * mm),
    para("Prepared from the current Plant Guardian repository, deployment documentation, and deployed GCP architecture.", "SmallPG"),
    PageBreak(),
]

story += heading("1. The complete system in one picture")
story += [
    para("The easiest mental model is: React and Next.js are the interface, FastAPI is the application brain, PostgreSQL is permanent memory, and GCP operates the production infrastructure."),
    code("""Browser
  -> Next.js frontend
       -> FastAPI backend
            -> SQLAlchemy
                 -> PostgreSQL

Vacation request
  -> Vacation Mode -> AI Assistance -> Groq

Automatic reminder
  -> Cloud Scheduler -> Backend -> Pub/Sub -> Web Push -> Browser"""),
]

if ARCHITECTURE_IMAGE.exists():
    story += [Spacer(1, 4), Image(str(ARCHITECTURE_IMAGE), width=174 * mm, height=127.15 * mm), Spacer(1, 4)]

story += [
    callout("Memory aid", "Next.js is the screen. FastAPI is the brain. PostgreSQL is memory. Cloud Run is the managed computer. Scheduler is the clock. Pub/Sub is the delivery queue. IAM is the security guard. Secret Manager is the vault."),
    PageBreak(),
]

story += heading("2. Frontend technology stack")
story += [
    sub("2.1 Next.js"),
    para("Next.js is the production web framework. It serves the dashboard, performs production optimization, and provides same-origin API rewrites. The browser requests paths such as /api/plants or /api/vacation-mode, while Next.js forwards them to the correct Cloud Run service."),
    callout("Why the proxy matters", "The browser normally sees one frontend origin. Backend and Vacation Mode addresses remain server-side, simplifying CORS and hiding service topology from ordinary browser links."),
    sub("2.2 React"),
    para("React supplies the interactive component model. It owns plant-card state, forms, dialogs, loading states, filters, toasts, watering updates, profile editing, and the floating growth companion. After Just Watered returns an updated plant, React replaces that record without reloading the page."),
    sub("2.3 TypeScript"),
    para("TypeScript gives the frontend strict contracts for Plant, UserProfile, CareEvent, payloads, status values, and response fields. It catches many mismatched-field and nullability mistakes before deployment."),
    sub("2.4 Tailwind CSS"),
    para("Tailwind defines the responsive grid, green theme, spacing, card surfaces, forms, focus states, status styling, and mobile behavior through reusable utility classes and CSS-variable design tokens."),
    sub("2.5 GSAP"),
    para("GSAP handles the three-stage plant-card flip with controlled timing and easing. It also supports animation cleanup and reduced-motion behavior."),
    sub("2.6 Phosphor Icons and inline SVG"),
    para("Phosphor provides consistent interface icons. The account plant companion is a React-generated inline SVG, allowing growth stage, leaves, flowers, pot face, and mood to change without downloading separate image files."),
    table(["Frontend responsibility", "Main technology"], [
        ["Page and production runtime", "Next.js"],
        ["Interactive components", "React"],
        ["Data contracts", "TypeScript"],
        ["Responsive visual system", "Tailwind CSS"],
        ["Card transitions", "GSAP"],
        ["Icons and plant character", "Phosphor Icons and inline SVG"],
    ], [70 * mm, 104 * mm]),
]

story += heading("3. Backend and database technology")
story += [
    sub("3.1 Python and FastAPI"),
    para("Python implements the domain logic. FastAPI exposes REST endpoints, authentication dependencies, structured errors, health checks, internal notification routes, and development API documentation."),
    sub("3.2 Pydantic"),
    para("Pydantic validates requests and responses. It ensures required fields exist, watering frequency is positive, enum-like values are valid, and frontend responses match the documented contract. Invalid requests normally return HTTP 422."),
    sub("3.3 SQLAlchemy"),
    para("SQLAlchemy maps Python models to PostgreSQL tables and handles queries, transactions, relationships, ownership filtering, and cascade deletion."),
    sub("3.4 Alembic"),
    para("Alembic manages database schema versions. The backend container runs alembic upgrade head before FastAPI starts, keeping a populated Cloud SQL database compatible with the deployed code."),
    sub("3.5 PostgreSQL"),
    para("PostgreSQL stores permanent state: users, password hashes, sessions, profiles, plants, waterings, care events, account XP, push subscriptions, and notification delivery records."),
    callout("Computed, not stored", "Risk score, days until due, seasonal effective frequency, status, and avatar mood are calculated at response time. This prevents values from becoming stale."),
    code("""Frontend request
  -> FastAPI route
       -> Pydantic validation
            -> service/business logic
                 -> SQLAlchemy transaction
                      -> PostgreSQL"""),
]

story += heading("4. Technology behind each product feature")
feature_rows = [
    ["Dashboard and plant cards", "Next.js, React, TypeScript, Tailwind"],
    ["Create, edit, and delete", "React form -> FastAPI -> Pydantic -> SQLAlchemy -> PostgreSQL"],
    ["Just Watered", "React API call -> FastAPI transaction -> watering event -> updated response"],
    ["Risk Score", "Pure Python risk calculation in the backend"],
    ["Healthy / Soon / Overdue", "Backend status mapping plus Tailwind visual treatment"],
    ["Search, room filter, sorting", "TypeScript query functions and React state"],
    ["Three-face card", "React component state and GSAP animation"],
    ["Plant facts and care guide", "Bundled curated plant catalogue served by the backend"],
    ["Ideal watering frequency", "Species catalogue match with a seven-day fallback"],
    ["Seasonal Shift Mode", "Pure Python seasonal factor service"],
    ["Pet-safety intelligence", "Curated JSON dataset, Python resolver, stored safety flags"],
    ["Email/password login", "FastAPI auth, password hashing, HttpOnly session cookie, PostgreSQL"],
    ["Google login", "Google Identity Services and backend ID-token verification"],
    ["Private garden", "Authenticated ownership queries using user IDs"],
    ["Care history", "Append-only PostgreSQL care-event records"],
    ["Garden streak", "Python account-wide weekly care calculation"],
    ["Growth avatar", "Backend XP and mood plus React inline SVG"],
    ["Vacation Mode", "Dedicated FastAPI service"],
    ["AI caretaker wording", "AI Assistance FastAPI service and Groq"],
    ["AI fallback", "Deterministic Python message builder"],
    ["Browser reminders", "Push API, service worker, VAPID, FastAPI"],
    ["Cloud reminders", "Cloud Scheduler, Pub/Sub, OIDC, Web Push"],
    ["Local environment", "Docker and Docker Compose"],
    ["Quality checks", "Pytest, FastAPI TestClient, Vitest, ESLint, Next.js build"],
]
story.append(table(["Feature", "Technology path"], feature_rows, [61 * mm, 113 * mm]))

story += heading("5. Core business services")
story += [
    sub("5.1 Risk service"),
    para("backend/app/services/risk.py calculates days since watered, days until due, risk score, and status. The risk calculation uses the effective seasonal frequency when supplied."),
    code("risk = min(100, days_since_watered / effective_frequency * 100)"),
    table(["Score", "Status", "Meaning"], [
        ["0-39", "Healthy", "Plant is comfortably inside its watering window."],
        ["40-69", "Needs Water Soon", "The due date is approaching."],
        ["70-100", "Overdue / High Risk", "The plant needs attention."],
    ], [28 * mm, 55 * mm, 91 * mm]),
    sub("5.2 Seasonal service"),
    para("backend/app/services/seasons.py determines the Indian tropical season from the current UTC month and converts the user-configured base frequency into an effective frequency."),
    table(["Season", "Months", "Factor"], [
        ["Summer", "March-June", "0.75"],
        ["Monsoon", "July-September", "1.25"],
        ["Post-monsoon", "October-November", "1.0"],
        ["Winter", "December-February", "1.4"],
    ], [55 * mm, 70 * mm, 49 * mm]),
    sub("5.3 Pet-safety service"),
    para("backend/app/services/pet_safety.py resolves a species against a curated static dataset. It returns safe, mild, or toxic flags, cat and dog toxicity, and placement advice. Safety facts are not generated by an LLM."),
    sub("5.4 Account streak service"),
    para("backend/app/services/account_streaks.py implements the garden-wide streak. At least 70 percent of the garden must receive care within the weekly window, one plant alone cannot advance it, and an overdue plant can break it."),
    sub("5.5 Plant service"),
    para("backend/app/services/plants.py coordinates plant queries, ownership, care calculations, watering, event creation, catalogue defaults, pet safety, seasonal context, and API response assembly."),
]

story += heading("6. AI services, local containers, and testing")
story += [
    sub("6.1 Vacation Mode"),
    para("The vacation_mode FastAPI service receives dates and selected plants, builds a deterministic watering schedule, applies seasonal cadence and pet warnings, and requests optional caretaker wording from AI Assistance."),
    sub("6.2 AI Assistance"),
    para("The ai_assistance FastAPI service is an isolated adapter around Groq. It receives structured care data, builds a controlled prompt, and returns natural-language instructions. It does not own risk, scheduling, streak, or pet-safety rules."),
    callout("Reliability rule", "If Groq is unavailable, Vacation Mode returns a deterministic fallback briefing. Core care decisions do not depend on the LLM."),
    sub("6.3 Docker and Docker Compose"),
    para("Docker packages each service with its runtime and dependencies. Docker Compose starts the frontend, backend, PostgreSQL, Vacation Mode, and AI Assistance together for local development."),
    code("""docker compose up --build

Local services:
  frontend       :3000
  backend        :8000
  ai-assistance  :8001
  vacation-mode  :8002
  PostgreSQL     :5432"""),
    sub("6.4 Testing"),
    para("Backend tests use Pytest and FastAPI TestClient with an isolated database. Frontend tests use Vitest. ESLint checks code quality, and next build verifies TypeScript and the production bundle."),
]

story += heading("7. GCP service 1: Cloud Run")
story += [
    para("Cloud Run hosts Docker images as managed HTTPS services. It creates immutable revisions, routes traffic, emits logs and metrics, and scales instances according to demand."),
    table(["Cloud Run service", "Responsibility"], [
        ["frontend", "Next.js dashboard and same-origin API proxy"],
        ["backend", "FastAPI auth, plants, care logic, database access, and notifications"],
        ["vacation-mode", "Vacation schedule and caretaker briefing composition"],
        ["ai-assistance", "Groq integration for natural-language care wording"],
    ], [52 * mm, 122 * mm]),
    callout("Project use", "The current frontend revision is frontend-00005-5d8 and receives 100 percent of frontend traffic. Frontend-only changes can be deployed without touching the backend or database."),
    sub("Why Cloud Run helps"),
    *bullets(["Automatic HTTPS", "Independent service deployment", "Revision history and rollback", "Request-based autoscaling", "Scale-to-zero support", "Integrated logs and metrics"]),
    para("Console: Cloud Run > Services"),
]

story += heading("8. GCP services 2-4: data and container delivery")
story += [
    sub("8.1 Cloud SQL"),
    para("Cloud SQL runs the production PostgreSQL database. Instance plant-guardian-db contains database plant_guardian. The backend connects through the Cloud SQL Unix socket and uses the Cloud SQL Client role."),
    callout("What it protects", "User accounts, profiles, plants, watering history, care events, subscriptions, and delivery records survive container restarts and Cloud Run revision changes."),
    para("Console: SQL > Instances"),
    sub("8.2 Artifact Registry"),
    para("Artifact Registry is the private Docker image warehouse. Repository plant-guardian stores versioned images for frontend, backend, vacation-mode, and ai-assistance."),
    code("asia-south1-docker.pkg.dev/gcp-hackathon-506604/plant-guardian/frontend:latest"),
    para("Console: Artifact Registry > Repositories"),
    sub("8.3 Cloud Build"),
    para("Cloud Build is the remote build factory. It receives source code, installs dependencies, runs the Dockerfile, builds the production application, and pushes the resulting image to Artifact Registry."),
    para("For the frontend, Cloud Build also injects API_URL, VACATION_API_URL, and NEXT_PUBLIC_GOOGLE_CLIENT_ID because these values are required during the Next.js production build."),
    para("Console: Cloud Build > History"),
]

story += heading("9. GCP services 5-6: secrets and identity")
story += [
    sub("9.1 Secret Manager"),
    para("Secret Manager is the secure runtime vault. Plant Guardian stores the Groq API key and optional VAPID private key there. Values are injected into authorized Cloud Run services rather than being committed to Git or baked into images."),
    callout("Not a secret", "The Google OAuth Web client ID is public configuration. It must match the frontend and backend, but it does not need Secret Manager."),
    para("Console: Security > Secret Manager"),
    sub("9.2 IAM and service accounts"),
    para("IAM applies least privilege. Each runtime or machine caller receives a dedicated identity with only the permissions needed for its job."),
    table(["Identity", "Attached to", "Access"], [
        ["plant-guardian-frontend", "Frontend Cloud Run", "No project data roles"],
        ["plant-guardian-backend", "Backend Cloud Run", "Cloud SQL, topic publisher, VAPID secret"],
        ["plant-guardian-vacation", "Vacation Mode", "Service runtime only"],
        ["plant-guardian-ai", "AI Assistance", "Groq secret accessor"],
        ["plant-guardian-scheduler", "Cloud Scheduler", "Backend Cloud Run invoker"],
        ["plant-guardian-pubsub-push", "Pub/Sub push", "Backend Cloud Run invoker"],
    ], [52 * mm, 55 * mm, 67 * mm]),
    callout("Security benefit", "A service cannot automatically access every GCP resource. Scheduler and Pub/Sub call protected backend endpoints using Google-signed OIDC tokens instead of shared passwords."),
    para("Console: IAM & Admin > IAM and Service Accounts"),
]

story += heading("10. GCP services 7-8: automatic reminders")
story += [
    sub("10.1 Cloud Scheduler"),
    para("Cloud Scheduler is the production clock. Job plant-guardian-notifications runs every 15 minutes and sends an authenticated POST request to /internal/notifications/dispatch."),
    para("The backend checks user reminder settings, local delivery time, plant due status, and whether that delivery has already been recorded."),
    para("Console: Cloud Scheduler > Jobs"),
    sub("10.2 Pub/Sub"),
    para("Pub/Sub is the asynchronous delivery queue. The backend publishes a small delivery reference to topic plant-care-notifications. Push subscription plant-care-notifications-push calls the protected backend worker, which loads the full data from PostgreSQL and performs Web Push."),
    code("""Cloud Scheduler
  -> backend dispatch scan
       -> Pub/Sub topic
            -> authenticated push subscription
                 -> backend delivery worker
                      -> browser Web Push"""),
    sub("Why Pub/Sub helps"),
    *bullets(["Decouples scanning from notification delivery", "Retries transient failures", "Allows Scheduler to finish quickly", "Supports idempotent delivery records", "Keeps plant and user data in PostgreSQL"]),
    callout("Activation condition", "The notification infrastructure is used when VAPID keys are configured. Without VAPID, the rest of Plant Guardian still deploys normally."),
    para("Console: Pub/Sub > Topics and Subscriptions"),
]

story += heading("11. Google OAuth and application authentication")
story += [
    para("Google OAuth is configured through Google Auth Platform. It is an authentication integration rather than one of the eight infrastructure services above."),
    code("""Continue with Google
  -> Google Identity Services returns ID token
       -> frontend sends token to FastAPI
            -> backend verifies signature and audience
                 -> backend creates or finds local account
                      -> HttpOnly Plant Guardian session cookie"""),
    table(["Configuration", "Location", "Purpose"], [
        ["NEXT_PUBLIC_GOOGLE_CLIENT_ID", "Frontend build", "Loads the correct Google Web client in the browser"],
        ["GOOGLE_CLIENT_ID", "Backend environment", "Expected audience while verifying the ID token"],
        ["Authorized JavaScript origins", "Google Auth Platform", "Permits localhost and the deployed frontend origin"],
        ["Test users", "Google Auth Platform", "Allows selected accounts while the OAuth app is in Testing"],
    ], [58 * mm, 55 * mm, 61 * mm]),
    callout("Data ownership", "Google proves the user's identity. Plant Guardian still owns the profile, pets, plants, watering history, XP, streak, and session data in PostgreSQL."),
]

story += heading("12. Local deployment versus GCP")
story += [
    table(["Concern", "Local development", "GCP production"], [
        ["Application containers", "Docker Compose", "Cloud Run"],
        ["Database", "PostgreSQL container", "Cloud SQL PostgreSQL"],
        ["Image build", "Local Docker build", "Cloud Build"],
        ["Image storage", "Local Docker cache", "Artifact Registry"],
        ["Secrets", ".env file", "Secret Manager and Cloud Run configuration"],
        ["Automatic schedule", "Manual/local trigger", "Cloud Scheduler"],
        ["Notification queue", "Optional direct delivery", "Pub/Sub push workflow"],
        ["Service identity", "Local environment", "IAM service accounts and OIDC"],
    ], [48 * mm, 61 * mm, 65 * mm]),
    sub("Deployment sequence"),
    code("""Source code
  -> Cloud Build
       -> Docker image
            -> Artifact Registry
                 -> Cloud Run revision
                      -> 100 percent traffic after verification"""),
    callout("Portability", "Docker keeps the application architecture consistent. Local containers are replaced by managed GCP runtimes without rewriting the core application."),
]

story.append(PageBreak())
story += heading("13. Interview-ready explanation")
story += [
    Paragraph("Plant Guardian is a containerized full-stack application built with Next.js, React and TypeScript on the frontend, and Python FastAPI, Pydantic and SQLAlchemy on the backend. PostgreSQL stores users, plants and watering history, while risk, seasonal frequency, pet safety and streak metrics are calculated by modular backend services. The system is deployed to four Cloud Run services, uses Cloud SQL for persistence, Cloud Build and Artifact Registry for container delivery, Secret Manager and IAM for security, and Cloud Scheduler with Pub/Sub for reliable browser reminders. Google OAuth provides optional sign-in, while Groq is isolated to non-critical caretaker wording.", styles["QuotePG"]),
    sub("Key design decisions to remember"),
    *bullets(["Core care calculations live on the backend, not in React.", "Calculated metrics are returned dynamically instead of stored stale.", "Safety facts come from curated static data, not AI.", "AI wording has a deterministic fallback.", "Each user has a private garden and account-level companion.", "Cloud services use dedicated least-privilege identities.", "Frontend, backend, Vacation Mode, and AI Assistance can be deployed independently."]),
    callout("One-line summary", "Plant Guardian combines a typed modern frontend, a modular Python API, durable PostgreSQL state, and managed event-driven GCP infrastructure to tell users not only whether a plant needs water, but how urgent that care is."),
    sub("Common interview questions"),
    table(["Question", "Strong answer"], [
        ["What is unique?", "A backend-calculated urgency score compares every plant on one 0-100 scale instead of showing only a due date."],
        ["Why not store risk score?", "It depends on the current date and seasonal frequency. Calculating it on each response prevents stale data."],
        ["Why separate AI services?", "Vacation scheduling remains deterministic, while optional LLM wording is isolated and can fail without breaking core care."],
        ["Why use Pub/Sub?", "It separates reminder scanning from delivery, supports retries, and keeps Scheduler requests short."],
        ["How is security handled?", "HttpOnly sessions, input validation, Secret Manager, dedicated IAM identities, OIDC callers, and private Cloud SQL access."],
        ["How can it scale?", "Stateless Cloud Run services scale independently while shared durable state remains in managed PostgreSQL."],
    ], [53 * mm, 121 * mm]),
]

doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    rightMargin=18 * mm,
    leftMargin=18 * mm,
    topMargin=20 * mm,
    bottomMargin=18 * mm,
    title="Plant Guardian Technology Stack and Google Cloud Study Guide",
    author="Plant Guardian",
    subject="Technology stack, feature mapping, architecture, and GCP services",
)
doc.build(story, onFirstPage=page_header_footer, onLaterPages=page_header_footer)
print(OUTPUT)
