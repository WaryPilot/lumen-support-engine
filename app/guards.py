from typing import Any
from app.config import settings


def should_ignore_email(email_data: dict[str, Any]) -> tuple[bool, str]:
    sender = email_data.get("sender_email", "").lower()
    if not sender:
        return True, "missing_sender"
    if settings.support_email and sender == settings.support_email.lower():
        return True, "self_email"
    if sender.startswith(("noreply@", "no-reply@", "mailer-daemon@", "postmaster@")):
        return True, "automated_sender"
    auto_submitted = email_data.get("auto_submitted", "").lower()
    if auto_submitted and auto_submitted != "no":
        return True, f"auto_submitted:{auto_submitted}"
    if email_data.get("list_unsubscribe"):
        return True, "mailing_list"
    if email_data.get("precedence", "").lower() in {"bulk", "junk", "list"}:
        return True, "bulk_precedence"
    if not email_data.get("body"):
        return True, "empty_body"
    return False, "ok"
