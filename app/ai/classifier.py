from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from app.ai.schemas import TriageResult
from app.config import settings

_provider = GoogleProvider(api_key=settings.google_api_key or settings.gemini_api_key)
_model = GoogleModel("gemini-3.5-flash-lite", provider=_provider)

triage_agent = Agent(
    _model,
    output_type=TriageResult,
    retries=1,
    system_prompt=(
        "You are an email triage router for Lumen Audio (Aura ANC Headphones & Pulse Studio Monitors). "
        "Classify the customer email. Set requires_human=True if the customer is angry, threatens a chargeback, "
        "reports physical breakage, or demands a policy exception."
    ),
)


async def classify_email(subject: str, body: str) -> TriageResult:
    result = await triage_agent.run(f"Subject: {subject}\n\nCustomer Email:\n{body}")
    return result.output
