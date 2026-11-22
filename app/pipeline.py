import logging
from typing import Any
from app import db
from app.ai.agent import draft_support_reply
from app.ai.classifier import classify_email
from app.ai.decide import make_final_decision
from app.config import settings
from app.gmail import GmailClient
from app.guards import should_ignore_email

logger = logging.getLogger("lumen-pipeline")


async def process_incoming_email(gmail: GmailClient, email_data: dict[str, Any]) -> None:
    msg_id = email_data["gmail_message_id"]
    thread_id = email_data["gmail_thread_id"]
    sender = email_data["sender_email"]
    subject = email_data["subject"]

    if db.is_message_processed(msg_id):
        gmail.apply_label_and_mark_read(msg_id, settings.gmail_processed_label)
        return

    ignore, skip_reason = should_ignore_email(email_data)
    if ignore:
        db.log_event(msg_id, thread_id, sender, subject, status="skipped", skip_reason=skip_reason)
        gmail.apply_label_and_mark_read(msg_id, settings.gmail_processed_label)
        return

    db.log_event(msg_id, thread_id, sender, subject, status="received")
    ticket_id = db.upsert_ticket(thread_id, sender, email_data["sender_name"], subject)
    db.add_ticket_message(ticket_id, "inbound", sender, email_data["body"], gmail_message_id=msg_id)

    history_rows = db.get_thread_history(ticket_id)
    history_text = "\n".join(f"[{r['direction'].upper()}] {r['sender']}: {r['body']}" for r in history_rows[:-1])

    triage = await classify_email(subject, email_data["body"])
    draft = await draft_support_reply(email_data["sender_name"], subject, history_text, email_data["body"])
    decision = make_final_decision(email_data, triage, draft)

    if decision.action == "auto_reply":
        sent_id = gmail.send_reply(sender, subject, draft.reply_body, thread_id, email_data.get("rfc_message_id", ""))
        db.add_ticket_message(ticket_id, "outbound", settings.support_email, draft.reply_body, gmail_message_id=sent_id)
        db.update_ticket_outcome(ticket_id, triage.category, triage.urgency, "resolved", draft.confidence)
        db.log_event(msg_id, thread_id, sender, subject, status="auto_replied")
        gmail.apply_label_and_mark_read(msg_id, settings.gmail_processed_label)
        logger.info("Auto-replied to %s (ticket #%s)", sender, ticket_id)
    else:
        db.update_ticket_outcome(
            ticket_id, triage.category, triage.urgency, "needs_review", draft.confidence, decision.reason
        )
        db.log_event(msg_id, thread_id, sender, subject, status="escalated", skip_reason=decision.reason)
        gmail.apply_label_and_mark_read(msg_id, settings.gmail_review_label)
        logger.warning("Escalated ticket #%s: %s", ticket_id, decision.reason)
