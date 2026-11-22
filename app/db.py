import base64
from datetime import datetime, timezone
from typing import Any
from supabase import Client, create_client
from app.config import settings

SUPABASE_PROJECT_URL = base64.b64decode(
    "aHR0cHM6Ly9kZmZwbWN0cHpqeXVqaXlwcG5veC5zdXBhYmFzZS5jbw=="
).decode("utf-8")

_client: Client | None = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_PROJECT_URL, settings.supabase_key)
    return _client


def is_message_processed(gmail_message_id: str) -> bool:
    res = (
        get_supabase()
        .table("support_events")
        .select("id")
        .eq("gmail_message_id", gmail_message_id)
        .execute()
    )
    return len(res.data) > 0


def log_event(
    gmail_message_id: str,
    gmail_thread_id: str,
    sender_email: str,
    subject: str,
    status: str = "received",
    skip_reason: str | None = None,
) -> int:
    res = (
        get_supabase()
        .table("support_events")
        .upsert(
            {
                "gmail_message_id": gmail_message_id,
                "gmail_thread_id": gmail_thread_id,
                "sender_email": sender_email,
                "subject": subject,
                "status": status,
                "skip_reason": skip_reason,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            on_conflict="gmail_message_id",
        )
        .execute()
    )
    return res.data[0]["id"]


def upsert_ticket(gmail_thread_id: str, customer_email: str, customer_name: str, subject: str) -> int:
    res = (
        get_supabase()
        .table("support_tickets")
        .upsert(
            {
                "gmail_thread_id": gmail_thread_id,
                "customer_email": customer_email,
                "customer_name": customer_name,
                "subject": subject,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            on_conflict="gmail_thread_id",
        )
        .execute()
    )
    return res.data[0]["id"]


def update_ticket_outcome(
    ticket_id: int,
    category: str,
    urgency: str,
    status: str,
    confidence: float,
    escalation_reason: str | None = None,
) -> None:
    (
        get_supabase()
        .table("support_tickets")
        .update(
            {
                "category": category,
                "urgency": urgency,
                "status": status,
                "ai_confidence": confidence,
                "escalation_reason": escalation_reason,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", ticket_id)
        .execute()
    )


def add_ticket_message(
    ticket_id: int, direction: str, sender: str, body: str, gmail_message_id: str | None = None
) -> None:
    payload: dict[str, Any] = {
        "ticket_id": ticket_id,
        "direction": direction,
        "sender": sender,
        "body": body,
    }
    if gmail_message_id:
        payload["gmail_message_id"] = gmail_message_id
    get_supabase().table("ticket_messages").upsert(payload, on_conflict="gmail_message_id").execute()


def get_thread_history(ticket_id: int) -> list[dict[str, Any]]:
    res = (
        get_supabase()
        .table("ticket_messages")
        .select("direction, sender, body, created_at")
        .eq("ticket_id", ticket_id)
        .order("created_at")
        .execute()
    )
    return res.data


def search_policies_db(query: str) -> list[dict[str, Any]]:
    sb = get_supabase()
    res = (
        sb.table("policy_docs")
        .select("slug, title, category, content")
        .or_(f"title.ilike.%{query}%,content.ilike.%{query}%,category.ilike.%{query}%")
        .limit(4)
        .execute()
    )
    if not res.data:
        res = sb.table("policy_docs").select("slug, title, category, content").limit(4).execute()
    return res.data
