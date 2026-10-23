"""Deliver approved content to social platforms or an email recipient.

External delivery is disabled by default. Set ``CONTENT_DELIVERY_ENABLED=true``
only after the human-review workflow has approved the draft and the relevant
platform credentials are configured in ``.env``.
"""

from dataclasses import dataclass
from email.message import EmailMessage
import os
import re
import smtplib
import ssl
from pathlib import Path


class DeliveryError(RuntimeError):
    """Raised when approved content cannot be delivered."""


class DeliveryDisabledError(DeliveryError):
    """Raised when external delivery has not been explicitly enabled."""


@dataclass(frozen=True)
class DeliveryResult:
    """Record the result of a delivery without exposing credentials."""

    channel: str
    external_id: str
    destination: str


def _load_environment() -> None:
    """Load .env when python-dotenv is available."""

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if not env_path.exists():
            return
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if key and key not in os.environ:
                os.environ[key] = value


def _required(*names: str) -> dict[str, str]:
    values = {name: os.getenv(name, "").strip() for name in names}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise DeliveryError(
            "Missing delivery configuration: " + ", ".join(missing)
        )
    return values


def _ensure_enabled() -> None:
    if os.getenv("CONTENT_DELIVERY_ENABLED", "false").lower() != "true":
        raise DeliveryDisabledError(
            "Content delivery is disabled. Set CONTENT_DELIVERY_ENABLED=true "
            "after human approval to enable external publishing."
        )


def _check_content(content: str) -> None:
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Approved content must be a non-empty string")


def _check_email(address: str) -> str:
    address = address.strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", address):
        raise ValueError("recipient_email must be a valid email address")
    return address


def _requests():
    try:
        import requests
    except ImportError as exc:
        raise DeliveryError(
            "The requests package is required for social delivery. "
            "Run: pip install -r requirements.txt"
        ) from exc
    return requests


def publish_linkedin(content: str) -> DeliveryResult:
    """Publish an approved text-only post to a LinkedIn member or organization."""

    _check_content(content)
    settings = _required(
        "LINKEDIN_ACCESS_TOKEN",
        "LINKEDIN_AUTHOR_URN",
        "LINKEDIN_VERSION",
    )
    requests = _requests()
    response = requests.post(
        "https://api.linkedin.com/rest/posts",
        headers={
            "Authorization": f"Bearer {settings['LINKEDIN_ACCESS_TOKEN']}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Linkedin-Version": settings["LINKEDIN_VERSION"],
            "Content-Type": "application/json",
        },
        json={
            "author": settings["LINKEDIN_AUTHOR_URN"],
            "commentary": content.strip(),
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        },
        timeout=30,
    )
    try:
        response.raise_for_status()
    except Exception as exc:
        raise DeliveryError(
            f"LinkedIn publishing failed with HTTP {response.status_code}."
        ) from exc
    return DeliveryResult(
        channel="linkedin",
        external_id=response.headers.get("x-restli-id", "created"),
        destination=settings["LINKEDIN_AUTHOR_URN"],
    )


def publish_instagram(content: str) -> DeliveryResult:
    """Publish an approved caption using a configured Instagram media URL.

    Instagram publishing requires media. Set ``INSTAGRAM_MEDIA_URL`` to a
    publicly reachable image or video URL; the approved content becomes its
    caption.
    """

    _check_content(content)
    settings = _required(
        "INSTAGRAM_ACCESS_TOKEN",
        "INSTAGRAM_USER_ID",
        "INSTAGRAM_MEDIA_URL",
        "META_GRAPH_VERSION",
    )
    requests = _requests()
    base_url = f"https://graph.facebook.com/{settings['META_GRAPH_VERSION']}"
    container = requests.post(
        f"{base_url}/{settings['INSTAGRAM_USER_ID']}/media",
        params={
            "image_url": settings["INSTAGRAM_MEDIA_URL"],
            "caption": content.strip(),
            "access_token": settings["INSTAGRAM_ACCESS_TOKEN"],
        },
        timeout=30,
    )
    try:
        container.raise_for_status()
        creation_id = container.json()["id"]
    except Exception as exc:
        raise DeliveryError("Instagram media container creation failed.") from exc

    published = requests.post(
        f"{base_url}/{settings['INSTAGRAM_USER_ID']}/media_publish",
        params={
            "creation_id": creation_id,
            "access_token": settings["INSTAGRAM_ACCESS_TOKEN"],
        },
        timeout=30,
    )
    try:
        published.raise_for_status()
        external_id = published.json().get("id", "published")
    except Exception as exc:
        raise DeliveryError("Instagram media publishing failed.") from exc
    return DeliveryResult(
        channel="instagram",
        external_id=external_id,
        destination=settings["INSTAGRAM_USER_ID"],
    )


def send_email(
    content: str,
    recipient_email: str,
    *,
    subject: str = "FREITAG content",
) -> DeliveryResult:
    """Send approved email/newsletter content to the entered email address."""

    _check_content(content)
    recipient = _check_email(recipient_email)
    settings = _required("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "EMAIL_FROM")
    try:
        port = int(os.getenv("SMTP_PORT", "587"))
    except ValueError as exc:
        raise DeliveryError("SMTP_PORT must be an integer") from exc

    message = EmailMessage()
    message["From"] = settings["EMAIL_FROM"]
    message["To"] = recipient
    message["Subject"] = subject.strip() or "FREITAG content"
    message.set_content(content.strip())
    security = os.getenv("SMTP_SECURITY", "starttls").strip().lower()
    try:
        if security == "ssl":
            smtp_client = smtplib.SMTP_SSL(
                settings["SMTP_HOST"],
                port,
                timeout=30,
                context=ssl.create_default_context(),
            )
        elif security in {"starttls", "tls"}:
            smtp_client = smtplib.SMTP(settings["SMTP_HOST"], port, timeout=30)
        else:
            raise DeliveryError(
                "SMTP_SECURITY must be 'starttls' (usually port 587) or "
                "'ssl' (usually port 465)."
            )

        with smtp_client as smtp:
            if security in {"starttls", "tls"}:
                smtp.starttls(context=ssl.create_default_context())
            smtp.login(settings["SMTP_USERNAME"], settings["SMTP_PASSWORD"])
            smtp.send_message(message)
    except Exception as exc:
        if isinstance(exc, DeliveryError):
            raise
        detail = str(exc).strip() or exc.__class__.__name__
        raise DeliveryError(
            "Email delivery failed: "
            f"{exc.__class__.__name__}: {detail}. "
            "Check SMTP host/port, security mode, username, password, "
            "and provider app-password settings."
        ) from exc

    return DeliveryResult(
        channel="email",
        external_id="sent",
        destination=recipient,
    )


def deliver_content(
    channel: str,
    content: str,
    *,
    recipient_email: str | None = None,
    subject: str = "FREITAG content",
) -> DeliveryResult:
    """Deliver approved content to the selected channel.

    ``recipient_email`` is required only for ``email`` and ``newsletter``.
    """

    _load_environment()
    _ensure_enabled()
    channel = channel.strip().lower().replace("-", "_")
    if channel == "linkedin":
        return publish_linkedin(content)
    if channel == "instagram":
        return publish_instagram(content)
    if channel in {"email", "newsletter"}:
        if not recipient_email:
            raise ValueError(
                f"recipient_email is required when channel is {channel}"
            )
        return send_email(content, recipient_email, subject=subject)
    raise ValueError(f"Unsupported delivery channel: {channel}")
