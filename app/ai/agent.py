from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from app.ai.schemas import DraftReply
from app.config import settings
from app.db import search_policies_db

_provider = GoogleProvider(api_key=settings.google_api_key or settings.gemini_api_key)
_model = GoogleModel("gemini-3.5-flash-lite", provider=_provider)

support_agent = Agent(
    _model,
    output_type=DraftReply,
    retries=1,
    system_prompt=(
        "You are a customer support specialist at Lumen Audio. Always call `lookup_company_policies` "
        "before answering product, warranty, return, or troubleshooting questions. Never invent specs. "
        "If sending a missing accessory, ask for their Order Number and Shipping Address. "
        "If policies do not clearly cover the request, set needs_escalation=True and confidence < 0.6."
    ),
)


@support_agent.tool
def lookup_company_policies(ctx: RunContext[None], search_query: str) -> str:
    """Search Lumen Audio's official product, troubleshooting, and warranty policy documents."""
    docs = search_policies_db(search_query)
    if not docs:
        return "No matching policy documents found."
    return "\n\n---\n\n".join(f"### {d['title']} (slug: {d['slug']})\n{d['content']}" for d in docs)


async def draft_support_reply(
    customer_name: str, subject: str, thread_history: str, latest_message: str
) -> DraftReply:
    prompt = (
        f"Customer: {customer_name}\nSubject: {subject}\n\n"
        f"History:\n{thread_history or 'None'}\n\nLatest Message:\n{latest_message}"
    )
    result = await support_agent.run(prompt)
    return result.output
