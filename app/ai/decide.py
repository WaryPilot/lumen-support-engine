from dataclasses import dataclass
from typing import Any
from app.ai.schemas import DraftReply, TriageResult


@dataclass
class Decision:
    action: str
    reason: str


def make_final_decision(email_data: dict[str, Any], triage: TriageResult, draft: DraftReply) -> Decision:
    if email_data.get("has_attachments"):
        return Decision(action="escalate", reason="Attachment detected; requires human inspection.")
    if triage.requires_human or triage.category == "escalation_required":
        return Decision(action="escalate", reason=f"Triage escalation: {triage.reasoning}")
    if draft.needs_escalation or draft.confidence < 0.75:
        return Decision(action="escalate", reason=draft.escalation_note or f"Low confidence ({draft.confidence:.2f})")
    if triage.category == "warranty_claim" and triage.urgency == "high":
        return Decision(action="escalate", reason="High-urgency warranty claim requires human review.")
    return Decision(action="auto_reply", reason="Passed all confidence and policy guardrails.")
