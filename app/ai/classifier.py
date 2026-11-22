import asyncio
import logging
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from app.ai.schemas import TriageResult
from app.config import settings

logger = logging.getLogger("lumen-triage")

_provider = GoogleProvider(api_key=settings.google_api_key or settings.gemini_api_key)
_MODEL_CANDIDATES = ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-2.0-flash-lite"]

_SYSTEM_PROMPT = (
    "You are an email triage router for Lumen Audio (Aura ANC Headphones & Pulse Studio Monitors). "
    "Classify the customer email. Set requires_human=True if the customer is angry, threatens a chargeback, "
    "reports physical breakage, or demands a policy exception."
)

_AGENTS = [
    Agent(GoogleModel(m, provider=_provider), output_type=TriageResult, system_prompt=_SYSTEM_PROMPT, retries=1)
    for m in _MODEL_CANDIDATES
]


async def classify_email(subject: str, body: str) -> TriageResult:
    prompt = f"Subject: {subject}\n\nCustomer Email:\n{body}"
    last_exc: Exception | None = None
    for idx, agent in enumerate(_AGENTS):
        for attempt in range(2):
            try:
                result = await agent.run(prompt)
                return result.output
            except ModelHTTPError as exc:
                last_exc = exc
                if exc.status_code in (404, 429, 503):
                    logger.warning(
                        "Triage model %s unavailable (%s), retrying/failing over...",
                        _MODEL_CANDIDATES[idx],
                        exc.status_code,
                    )
                    await asyncio.sleep(2 * (attempt + 1))
                    if exc.status_code in (404, 429):
                        break
                    continue
                raise
    raise last_exc or RuntimeError("All triage models failed")
