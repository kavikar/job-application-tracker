"""Gmail I/O. Unlike classifier.py/matcher.py, this module is NOT
pure -- it makes real network calls -- so it's isolated behind the
same FastAPI dependency-injection pattern as get_db (see app/db.py):
tests override get_gmail_client with a fake, never a live call.
"""

import base64
import re
from dataclasses import dataclass
from email import message_from_bytes
from email.message import Message

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config import Settings, get_settings

GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"

# Below this length, treat a text/plain MIME part as unusable and fall
# back to stripping the text/html part instead. Not a guess: a real
# LinkedIn rejection email's plaintext part decoded to ~0 characters of
# actual message content (just unsubscribe-footer boilerplate) while
# the real "unfortunately, we will not be moving forward" sentence
# existed only in the HTML part. Found by checking the classifier
# against a real inbox during Phase 3, not by inspection.
_MIN_USABLE_PLAINTEXT_LENGTH = 40


@dataclass(frozen=True)
class RawEmail:
    message_id: str
    subject: str
    sender: str
    body: str


def extract_text(mime: Message) -> str:
    plain_parts: list[str] = []
    html_parts: list[str] = []

    parts = mime.walk() if mime.is_multipart() else [mime]
    for part in parts:
        content_type = part.get_content_type()
        if content_type == "text/plain":
            plain_parts.append(_decode_part(part))
        elif content_type == "text/html":
            html_parts.append(_decode_part(part))

    plain_text = "\n".join(p for p in plain_parts if p).strip()
    if len(plain_text) >= _MIN_USABLE_PLAINTEXT_LENGTH:
        return plain_text

    html_text = "\n".join(_strip_html(h) for h in html_parts if h).strip()
    return html_text or plain_text


def _decode_part(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    charset = part.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def _strip_html(html: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_credentials(settings: Settings) -> Credentials:
    return Credentials(
        token=None,
        refresh_token=settings.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=[GMAIL_READONLY_SCOPE],
    )


class GmailClient:
    def __init__(self, credentials: Credentials):
        self._service = build("gmail", "v1", credentials=credentials)

    def list_recent_messages(self, query: str) -> list[RawEmail]:
        results = (
            self._service.users()
            .messages()
            .list(userId="me", q=query)
            .execute()
        )
        return [self._fetch(m["id"]) for m in results.get("messages", [])]

    def _fetch(self, message_id: str) -> RawEmail:
        raw = (
            self._service.users()
            .messages()
            .get(userId="me", id=message_id, format="raw")
            .execute()
        )
        mime = message_from_bytes(base64.urlsafe_b64decode(raw["raw"]))
        return RawEmail(
            message_id=message_id,
            subject=mime.get("Subject", ""),
            sender=mime.get("From", ""),
            body=extract_text(mime),
        )


def get_gmail_client() -> GmailClient:
    return GmailClient(load_credentials(get_settings()))
