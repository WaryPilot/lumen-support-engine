import base64
from email.message import EmailMessage
from email.utils import parseaddr
from typing import Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.config import settings

SCOPES = [
    base64.b64decode("aHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vYXV0aC9nbWFpbC5tb2RpZnk=").decode("utf-8")
]
TOKEN_URI = base64.b64decode("aHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4=").decode("utf-8")


class GmailClient:
    def __init__(self) -> None:
        creds = Credentials(
            token=None,
            refresh_token=settings.google_refresh_token,
            token_uri=TOKEN_URI,
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=SCOPES,
        )
        creds.refresh(Request())
        self.service = build("gmail", "v1", credentials=creds)
        self._label_cache: dict[str, str] = {}

    def get_or_create_label(self, label_name: str) -> str:
        if label_name in self._label_cache:
            return self._label_cache[label_name]
        results = self.service.users().labels().list(userId="me").execute()
        for lbl in results.get("labels", []):
            self._label_cache[lbl["name"]] = lbl["id"]
        if label_name in self._label_cache:
            return self._label_cache[label_name]
        created = (
            self.service.users()
            .labels()
            .create(
                userId="me",
                body={"name": label_name, "labelListVisibility": "labelShow", "messageListVisibility": "show"},
            )
            .execute()
        )
        self._label_cache[label_name] = created["id"]
        return created["id"]

    def fetch_unprocessed_messages(self, max_results: int = 10) -> list[dict[str, Any]]:
        query = f'is:unread -label:"{settings.gmail_processed_label}" -label:"{settings.gmail_review_label}"'
        resp = self.service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        parsed: list[dict[str, Any]] = []
        for item in resp.get("messages", []):
            msg = self.service.users().messages().get(userId="me", id=item["id"], format="full").execute()
            parsed.append(self._parse_message(msg))
        return parsed

    def _parse_message(self, msg: dict[str, Any]) -> dict[str, Any]:
        payload = msg.get("payload", {})
        headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
        sender_name, sender_email = parseaddr(headers.get("from", ""))
        body_text, has_attachments = self._extract_body_and_attachments(payload)
        return {
            "gmail_message_id": msg["id"],
            "gmail_thread_id": msg["threadId"],
            "rfc_message_id": headers.get("message-id", ""),
            "subject": headers.get("subject", "(No Subject)"),
            "sender_name": sender_name or sender_email,
            "sender_email": sender_email.lower(),
            "auto_submitted": headers.get("auto-submitted", ""),
            "precedence": headers.get("precedence", ""),
            "list_unsubscribe": headers.get("list-unsubscribe", ""),
            "body": body_text.strip(),
            "has_attachments": has_attachments,
        }

    def _extract_body_and_attachments(self, payload: dict[str, Any]) -> tuple[str, bool]:
        plain_parts: list[str] = []
        has_attachments = False

        def walk(part: dict[str, Any]) -> None:
            nonlocal has_attachments
            if part.get("filename"):
                has_attachments = True
            data = part.get("body", {}).get("data")
            if part.get("mimeType") == "text/plain" and data:
                plain_parts.append(base64.urlsafe_b64decode(data).decode("utf-8", errors="replace"))
            for sub in part.get("parts", []):
                walk(sub)

        walk(payload)
        return "\n".join(plain_parts), has_attachments

    def send_reply(self, to_email: str, subject: str, body: str, thread_id: str, in_reply_to: str = "") -> str:
        msg = EmailMessage()
        msg["To"] = to_email
        msg["From"] = settings.support_email
        msg["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
            msg["References"] = in_reply_to
        msg.set_content(body)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        sent = self.service.users().messages().send(userId="me", body={"raw": raw, "threadId": thread_id}).execute()
        return sent["id"]

    def apply_label_and_mark_read(self, message_id: str, label_name: str) -> None:
        label_id = self.get_or_create_label(label_name)
        self.service.users().messages().modify(
            userId="me", id=message_id, body={"addLabelIds": [label_id], "removeLabelIds": ["UNREAD"]}
        ).execute()
