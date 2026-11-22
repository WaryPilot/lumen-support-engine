import asyncio
import logging
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from app.ai.schemas import DraftReply
from app.config import settings
from app.db import search_policies_db

logger = logging.getLogger("lumen-agent")

_provider = GoogleProvider(api_key=settings.google_api_key or settings.gemini_api_key)
_MODEL_CANDIDATES = ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-2.0-flash-lite"]

_SYSTEM_PROMPT = (
    "You are a customer support specialist at Lumen Audio. Always call `lookup_company_policies` "
    "before answering product, warranty, return, or troubleshooting questions. Never invent specs. "
    "If sending a missing accessory, ask for their Order Number and Shipping Address. "
    "If policies do not clearly cover the request, set needs_escalation=True and confidence < 0.6."
)


def _build_agent(model_name: str) -> Agent[None, DraftReply]:
    agent = Agent(
        GoogleModel(model_name, provider=_provider),
        output_type=DraftReply,
        system_prompt=_SYSTEM_PROMPT,
        retries=1,
    )

    @agent.tool
    def lookup_company_policies(ctx: RunContext[None], search_query: str) -> str:
        """Search Lumen Audio's official product, troubleshooting, and warranty policy documents."""
        docs = search_policies_db(search_query)
        if not docs:
            return "No matching policy documents found."
        return "\n\n---\n\n".join(f"### {d['title']} (slug: {d['slug']})\n{d['content']}" for d in docs)

    return agent


_AGENTS = [_build_agent(m) for m in _MODEL_CANDIDATES]


async def draft_support_reply(
    customer_name: str, subject: str, thread_history: str, latest_message: str
) -> DraftReply:
    prompt = (
        f"Customer: {customer_name}\nSubject: {subject}\n\n"
        f"History:\n{thread_history or 'None'}\n\nLatest Message:\n{latest_message}"
    )
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
                        "Resolution model %s unavailable (%s), retrying/failing over...",
                        _MODEL_CANDIDATES[idx],
                        exc.status_code,
                    )
                    await asyncio.sleep(2 * (attempt + 1))
                    if exc.status_code in (404, 429):
                        break
                    continue
                raise
    raise last_exc or RuntimeError("All resolution models failed")
