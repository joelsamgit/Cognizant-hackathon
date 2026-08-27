from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "architecture" / "plant-guardian-gcp-architecture.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

W, H = 2600, 1900
BG = "#EAF6ED"
DEEP = "#155A36"
DARK = "#1F6B43"
MID = "#58A873"
LIGHT = "#CFEFD6"
PALE = "#F6FCF7"
INK = "#123D27"
MUTED = "#47745A"
LINE = "#6EBB83"

FONT_DIR = Path("C:/Windows/Fonts")
REGULAR = str(FONT_DIR / "segoeui.ttf")
BOLD = str(FONT_DIR / "segoeuib.ttf")


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else REGULAR, size)


image = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(image)


def text(x, y, value, size=22, color=INK, bold=False, anchor=None):
    draw.text((x, y), value, font=font(size, bold), fill=color, anchor=anchor)


def wrapped(x, y, value, width, size=18, color=MUTED, bold=False, gap=4):
    f = font(size, bold)
    lines = []
    line = ""
    for word in value.split():
        candidate = f"{line} {word}".strip()
        if not line or draw.textbbox((0, 0), candidate, font=f)[2] <= width:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    for index, line in enumerate(lines):
        draw.text((x, y + index * (size + gap)), line, font=f, fill=color)


def dashed_segment(p1, p2, color=MID, width=5):
    x1, y1 = p1
    x2, y2 = p2
    distance = max(abs(x2 - x1), abs(y2 - y1))
    steps = max(1, int(distance / 18))
    for index in range(steps):
        if index % 2 == 0:
            a = index / steps
            b = min(1, (index + 1) / steps)
            draw.line((x1 + (x2 - x1) * a, y1 + (y2 - y1) * a, x1 + (x2 - x1) * b, y1 + (y2 - y1) * b), fill=color, width=width)


def connector(points, label=None, label_pos=None, dashed=False, color=DEEP, width=5):
    for start, end in zip(points, points[1:]):
        if dashed:
            dashed_segment(start, end, color=color, width=width)
        else:
            draw.line((*start, *end), fill=color, width=width)
    start, end = points[-2], points[-1]
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 16
    p2 = (end[0] - size * math.cos(angle - 0.5), end[1] - size * math.sin(angle - 0.5))
    p3 = (end[0] - size * math.cos(angle + 0.5), end[1] - size * math.sin(angle + 0.5))
    draw.polygon([end, p2, p3], fill=color)
    if label:
        x, y = label_pos or ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 - 22)
        text(x, y, label, size=15, color=MUTED, bold=True, anchor="mm")


def box(x, y, w, h, title, subtitle, kind="service", tags=None):
    fill = DARK if kind == "core" else PALE
    outline = DEEP if kind in {"core", "external"} else LINE
    title_color = "#FFFFFF" if kind == "core" else DEEP
    subtitle_color = "#DDF5E2" if kind == "core" else MUTED
    draw.rounded_rectangle((x + 8, y + 10, x + w + 8, y + h + 10), radius=24, fill="#B8D9C1")
    draw.rounded_rectangle((x, y, x + w, y + h), radius=24, fill=fill, outline=outline, width=3)
    draw.rounded_rectangle((x + 24, y + 22, x + 70, y + 68), radius=12, fill=LIGHT if kind != "core" else MID)
    icon_fill = DEEP if kind != "core" else "#FFFFFF"
    draw.ellipse((x + 37, y + 31, x + 56, y + 51), fill=icon_fill)
    draw.line((x + 47, y + 49, x + 47, y + 59), fill=icon_fill, width=3)
    text(x + 88, y + 24, title, size=25, color=title_color, bold=True)
    wrapped(x + 26, y + 84, subtitle, w - 52, size=18, color=subtitle_color)
    if tags:
        tag_x = x + 26
        tag_y = y + h - 44
        for tag in tags:
            tag_w = draw.textbbox((0, 0), tag, font=font(15, True))[2] + 24
            if tag_x + tag_w > x + w - 22:
                tag_x = x + 26
                tag_y -= 32
            draw.rounded_rectangle((tag_x, tag_y, tag_x + tag_w, tag_y + 28), radius=14, fill=LIGHT if kind != "core" else MID)
            text(tag_x + 12, tag_y + 5, tag, size=15, color=DEEP if kind != "core" else "#FFFFFF", bold=True)
            tag_x += tag_w + 9


def section_label(x, y, value, width=280):
    draw.rounded_rectangle((x, y, x + width, y + 34), radius=17, fill=LIGHT)
    text(x + 18, y + 7, value.upper(), size=14, color=DEEP, bold=True)


# Header
text(110, 54, "PLANT GUARDIAN", size=16, color=MID, bold=True)
text(110, 85, "Production architecture on Google Cloud", size=42, color=DEEP, bold=True)
wrapped(112, 145, "A stateless plant-care platform: Next.js dashboard, FastAPI services, PostgreSQL state, secure identities, and event-driven reminders.", 1450, size=21, color=MUTED)
draw.line((110, 210, 2490, 210), fill=LINE, width=3)

# Lane labels
section_label(120, 245, "User experience")
section_label(650, 245, "Application runtime", width=300)
section_label(2020, 245, "Managed data + identity", width=360)
section_label(120, 655, "Optional guidance lane", width=310)
section_label(120, 965, "Identity + secrets", width=280)
section_label(120, 1235, "Scheduled notifications", width=330)
section_label(120, 1555, "Container delivery", width=280)

# Connectors are drawn first so blocks remain clean and readable.
connector([(500, 425), (650, 425)], label="HTTPS", label_pos=(575, 398))
connector([(1150, 425), (1290, 425)], label="/api", label_pos=(1220, 398))
connector([(1850, 425), (2020, 425)], label="SQL", label_pos=(1935, 398))

connector([(1570, 600), (1570, 650), (1180, 650), (1180, 735)], label="care data", label_pos=(1330, 625))
connector([(1140, 820), (1290, 820)], label="structured prompt", label_pos=(1215, 792))
connector([(1850, 820), (2020, 820)], label="HTTPS", label_pos=(1935, 792))
connector([(900, 585), (900, 735)], dashed=True, color=MID, label="/api/vacation-mode", label_pos=(1000, 660))

connector([(500, 500), (560, 620), (560, 900), (520, 1035)], dashed=True, color=MID, label="ID token", label_pos=(625, 900))
connector([(1290, 565), (600, 565), (600, 930), (520, 1035)], dashed=True, color=MID, label="validate audience", label_pos=(720, 930))
connector([(1850, 565), (1910, 565), (1910, 930), (1850, 1035)], dashed=True, color=MID, label="service identity", label_pos=(1990, 930))
connector([(2260, 565), (2260, 1035)], dashed=True, color=MID, label="runtime secret", label_pos=(2340, 800))

connector([(520, 1380), (670, 1380)], label="dispatch", label_pos=(595, 1353))
connector([(1170, 1380), (1320, 1380)], label="event", label_pos=(1245, 1353))
connector([(1860, 1380), (2020, 1380)], label="push", label_pos=(1940, 1353))
connector([(520, 1270), (560, 1270), (560, 1190), (1570, 1190), (1570, 1035)], dashed=True, color=MID, label="OIDC trigger", label_pos=(900, 1165))

connector([(620, 1655), (730, 1655)], label="push image", label_pos=(675, 1628))
connector([(1250, 1655), (1360, 1655)], label="deploy", label_pos=(1305, 1628))
connector([(1880, 1655), (1990, 1655)], dashed=True, color=MID, label="config", label_pos=(1935, 1628))

# Top row blocks
box(120, 315, 380, 230, "Browser", "Plant owners use the responsive dashboard, profile, reminders, search, CRUD, and watering actions.", kind="core", tags=["HTTPS", "Web Push"])
box(650, 315, 500, 270, "Frontend", "Next.js on Cloud Run. Serves the UI and proxies /api requests to private service URLs.", tags=["Cloud Run", "Next.js"])
box(1290, 285, 560, 315, "Backend API", "FastAPI owns sessions, profiles, plant CRUD, risk scoring, streaks, pet safety, seasons, and notification dispatch.", kind="core", tags=["FastAPI", "SQLAlchemy"])
box(2020, 325, 460, 240, "Cloud SQL", "Managed PostgreSQL stores users, plants, watering history, browser subscriptions, and delivery records.", tags=["Postgres", "Private socket"])

# Guidance row blocks
box(650, 735, 490, 235, "Vacation Mode", "Creates caretaker briefings from structured plant care data, seasonal adjustments, and pet-safety context.", tags=["Cloud Run", "Internal URL"])
box(1290, 735, 560, 235, "AI Assistant", "Isolated FastAPI adapter that requests wording from Groq without owning plant data or business rules.", tags=["Cloud Run", "Groq"])
box(2020, 735, 460, 205, "Groq API", "External language model endpoint. The API key is injected at runtime from Secret Manager.", kind="external", tags=["External API", "Secret"])

# Identity and secrets row blocks
box(120, 1035, 400, 170, "Google OAuth", "Google Identity Services supplies an ID token. The backend validates the audience and starts the session.", kind="external", tags=["Web client", "OIDC"])
box(1290, 1035, 560, 170, "IAM + service accounts", "Least-privilege identities for Cloud Run, Cloud SQL, Scheduler, Pub/Sub push, and secret access.", kind="core", tags=["OIDC", "Least privilege"])
box(2020, 1035, 460, 170, "Secret Manager", "Groq and optional VAPID secrets are injected at runtime; values are never baked into images.", tags=["Runtime secrets"])

# Notification row blocks
box(120, 1270, 400, 220, "Cloud Scheduler", "Runs every 15 minutes in UTC and calls the protected dispatch endpoint with an OIDC identity.", tags=["OIDC", "15 min"])
box(670, 1270, 500, 220, "Dispatch + Web Push", "Backend finds due plants, records idempotent deliveries, and sends browser notifications when enabled.", tags=["Backend route", "VAPID"])
box(1320, 1270, 540, 220, "Pub/Sub", "Durable asynchronous topic and authenticated push subscription for notification delivery and retries.", tags=["Topic", "Push subscription"])
box(2020, 1270, 460, 220, "Browser notification", "The user receives a care reminder even when the dashboard tab is closed, subject to browser permission and service-worker support.", kind="external", tags=["Permission", "Service worker"])

# Delivery row blocks
box(120, 1585, 500, 180, "Cloud Build", "Builds Docker images from the repository whenever a full or single-service deploy is submitted.", tags=["Build steps", "Logs"])
box(730, 1585, 520, 180, "Artifact Registry", "Private regional repository stores versioned frontend, backend, vacation-mode, and ai-assistance images.", tags=["Docker", "asia-south1"])
box(1360, 1585, 520, 180, "Cloud Run revisions", "Deploys immutable revisions, routes traffic, autos-scales instances, and supports rollback.", kind="core", tags=["Revisions", "Scale to zero"])
box(1990, 1585, 490, 180, "Configuration", "Environment variables, Cloud SQL attachment, CORS, OAuth client IDs, and service URLs are supplied per environment.", tags=[".env", "Deploy args"])

# Footer legend
draw.line((120, 1800, 2480, 1800), fill=LINE, width=2)
text(120, 1812, "Solid arrows = application/data flow", size=16, color=MUTED)
text(670, 1812, "Dashed arrows = identity/configuration/deployment", size=16, color=MUTED)
text(2020, 1812, "Primary region: asia-south1 (Mumbai)", size=16, color=MUTED, bold=True)

image.save(OUT, "PNG", optimize=True)
print(OUT)
