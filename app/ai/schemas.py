from typing import Literal
from pydantic import BaseModel, Field


class TriageResult(BaseModel):
    category: Literal["troubleshooting", "warranty_claim", "order_issue", "pre_sales", "escalation_required"]
    urgency: Literal["low", "normal", "high"]
    requires_human: bool
    reasoning: str


class DraftReply(BaseModel):
    reply_body: str = Field(description="Helpful, concise email reply signed as 'Lumen Audio Support Team'.")
    confidence: float = Field(ge=0.0, le=1.0)
    cited_policies: list[str] = Field(default_factory=list)
    needs_escalation: bool = False
    escalation_note: str | None = None
