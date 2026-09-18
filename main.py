import json
import logging
import os
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from email_validator import EmailNotValidError, validate_email
from fastapi import BackgroundTasks, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

load_dotenv()

logger = logging.getLogger("matsi_counselling")
logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
SUBMISSIONS_FILE = DATA_DIR / "submissions.jsonl"

PRACTICE_EMAIL = "matsicounselling@gmail.com"

INTEREST_LABELS = {
    "initial_call": "Initial Call",
    "counselling_session": "Counselling Session",
}
COUNSELLING_TYPE_LABELS = {
    "individual": "Individual Counselling",
    "relationship": "Relationship Counselling",
}

MAX_REQUEST_BODY_BYTES = 20_000
RATE_LIMIT_WINDOW_SECONDS = 600
RATE_LIMIT_MAX_SUBMISSIONS = 3
_contact_rate_limit_hits: dict[str, list[float]] = defaultdict(list)

app = FastAPI(title="Matsi Counselling")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.middleware("http")
async def enforce_body_size_limit(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_BODY_BYTES:
        return PlainTextResponse("Request entity too large", status_code=413)
    return await call_next(request)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    return response


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def is_rate_limited(ip: str) -> bool:
    now = time.monotonic()
    hits = _contact_rate_limit_hits[ip]
    hits[:] = [t for t in hits if now - t < RATE_LIMIT_WINDOW_SECONDS]
    if len(hits) >= RATE_LIMIT_MAX_SUBMISSIONS:
        return True
    hits.append(now)
    return False


def render(request: Request, template: str, active_page: str, **context):
    return templates.TemplateResponse(
        request,
        template,
        {
            "active_page": active_page,
            "current_year": datetime.now(timezone.utc).year,
            **context,
        },
    )


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return render(request, "index.html", "home")


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return render(request, "about.html", "about")


@app.get("/approach", response_class=HTMLResponse)
async def approach(request: Request):
    return render(request, "approach.html", "approach")


@app.get("/services", response_class=HTMLResponse)
async def services(request: Request):
    return render(request, "services.html", "services")


@app.get("/practice-principles", response_class=HTMLResponse)
async def principles(request: Request):
    return render(request, "principles.html", "principles")


@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return render(request, "contact.html", "contact")


def validate_contact_form(name, email, interest, counselling_type, agree):
    errors = {}

    if not name or not name.strip():
        errors["name"] = "Please enter your name."

    if not email or not email.strip():
        errors["email"] = "Please enter your email address."
    else:
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            errors["email"] = "Please enter a valid email address."

    if interest not in INTEREST_LABELS:
        errors["interest"] = "Please let me know what you're interested in."

    if counselling_type not in COUNSELLING_TYPE_LABELS:
        errors["counselling_type"] = "Please select a type of counselling."

    if not agree:
        errors["agree"] = "Please confirm you agree to the Practice Principles."

    return errors


def store_submission(record: dict) -> None:
    with SUBMISSIONS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _send_via_resend(api_key: str, from_email: str, to: str, subject: str, text: str) -> None:
    payload = json.dumps({"from": from_email, "to": [to], "subject": subject, "text": text}).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            response.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        logger.error("Resend API error %s sending to %s: %s", e.code, to, body)
        raise


def send_emails(record: dict) -> None:
    """Send a confirmation email to the visitor and a notification to the
    practice via Resend's HTTPS API. Raw SMTP doesn't work on most PaaS free
    tiers (outbound SMTP ports are commonly blocked), so this goes over
    HTTPS instead. No-ops (and logs) if RESEND_API_KEY isn't configured yet."""

    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("FROM_EMAIL", "Matsi Counselling <hello@matsicounselling.com>")

    if not api_key:
        logger.info(
            "RESEND_API_KEY not configured — skipping email send for submission from %s",
            record["email"],
        )
        return

    visitor_text = (
        "Thank you for getting in touch with Matsi Counselling.\n\n"
        "I've received your message and will get back to you as soon as "
        "possible to arrange a suitable time for our appointment.\n\n"
        "Warmly,\nAnna Matsi\nMatsi Counselling"
    )

    notify_text = (
        "New submission from the Matsi Counselling contact form:\n\n"
        f"Name: {record['name']}\n"
        f"Email: {record['email']}\n"
        f"Interested in: {INTEREST_LABELS.get(record['interest'], record['interest'])}\n"
        f"Type of counselling: "
        f"{COUNSELLING_TYPE_LABELS.get(record['counselling_type'], record['counselling_type'])}\n"
        f"Message: {record.get('message') or '(none)'}\n"
    )

    try:
        _send_via_resend(
            api_key, from_email, record["email"],
            "Thank you for getting in touch — Matsi Counselling", visitor_text,
        )
        _send_via_resend(
            api_key, from_email, PRACTICE_EMAIL,
            f"New contact form submission from {record['name']}", notify_text,
        )
        logger.info("Contact form emails sent successfully for submission from %s", record["email"])
    except Exception:
        logger.exception("Failed to send contact form emails")


@app.post("/contact", response_class=HTMLResponse)
async def contact_submit(
    request: Request,
    background_tasks: BackgroundTasks,
    name: Annotated[str, Form(max_length=150)] = "",
    email: Annotated[str, Form(max_length=254)] = "",
    interest: str = Form(""),
    counselling_type: str = Form(""),
    message: Annotated[str, Form(max_length=3000)] = "",
    agree: str | None = Form(None),
    website: Annotated[str, Form(max_length=254)] = "",
):
    # Honeypot: real visitors never see or fill this field. Treat a filled
    # value as spam and silently show the normal confirmation, without
    # storing or emailing anything.
    if website.strip():
        logger.warning("Contact form honeypot triggered from %s", get_client_ip(request))
        return render(request, "contact.html", "contact", submitted=True)

    client_ip = get_client_ip(request)
    if is_rate_limited(client_ip):
        logger.warning("Contact form rate limit hit from %s", client_ip)
        return render(
            request,
            "contact.html",
            "contact",
            errors={
                "form": "Too many submissions from this address. Please try again in a little while, "
                "or email us directly at matsicounselling@gmail.com."
            },
            form_data={
                "name": name,
                "email": email,
                "interest": interest,
                "counselling_type": counselling_type,
                "message": message,
                "agree": bool(agree),
            },
        )

    errors = validate_contact_form(name, email, interest, counselling_type, agree)

    if errors:
        return render(
            request,
            "contact.html",
            "contact",
            errors=errors,
            form_data={
                "name": name,
                "email": email,
                "interest": interest,
                "counselling_type": counselling_type,
                "message": message,
                "agree": bool(agree),
            },
        )

    record = {
        "name": name.strip(),
        "email": email.strip(),
        "interest": interest,
        "counselling_type": counselling_type,
        "message": message.strip(),
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    store_submission(record)
    background_tasks.add_task(send_emails, record)

    return render(request, "contact.html", "contact", submitted=True)
