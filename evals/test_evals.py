import asyncio
import logging
from dataclasses import dataclass
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from app.ai.agent import draft_support_reply
from app.ai.classifier import classify_email
from app.ai.decide import make_final_decision

logging.getLogger("httpx").setLevel(logging.WARNING)


@dataclass
class ActionMatches(Evaluator[dict, str]):
    def evaluate(self, ctx: EvaluatorContext[dict, str]) -> bool:
        return ctx.output == ctx.expected_output


dataset = Dataset(
    name="lumen_audio_support_golden_evals",
    cases=[
        Case(
            name="multipoint_bluetooth_howto",
            inputs={
                "subject": "Connect Aura ANC to laptop and phone",
                "body": "Hi, how do I pair my Aura ANC headphones to two devices at once?",
                "has_attachments": False,
            },
            expected_output="auto_reply",
        ),
        Case(
            name="desk_sizing_pulse_monitors",
            inputs={
                "subject": "Pulse 4 or Pulse 5 for small desk?",
                "body": "My desk is 100cm wide. Which Pulse studio monitors fit best?",
                "has_attachments": False,
            },
            expected_output="auto_reply",
        ),
        Case(
            name="missing_flight_adapter",
            inputs={
                "subject": "Missing airplane adapter in box",
                "body": "I opened my Aura ANC box and the airplane dual-prong adapter is missing. Can you ship one?",
                "has_attachments": False,
            },
            expected_output="auto_reply",
        ),
        Case(
            name="cracked_headband_with_photo",
            inputs={
                "subject": "Headband snapped",
                "body": "My headphones cracked when I dropped them, see attached photo.",
                "has_attachments": True,
            },
            expected_output="escalate",
        ),
        Case(
            name="angry_chargeback_threat",
            inputs={
                "subject": "DISPUTING CHARGE NOW",
                "body": "This is ridiculous, refund me immediately or I am filing a chargeback with my bank.",
                "has_attachments": False,
            },
            expected_output="escalate",
        ),
    ],
    evaluators=[ActionMatches()],
)


async def run_pipeline_decision(inputs: dict) -> str:
    triage = await classify_email(inputs["subject"], inputs["body"])
    draft = await draft_support_reply(
        customer_name="Test Customer",
        subject=inputs["subject"],
        thread_history="",
        latest_message=inputs["body"],
    )
    decision = make_final_decision(inputs, triage, draft)
    await asyncio.sleep(3)
    return decision.action


if __name__ == "__main__":
    report = asyncio.run(dataset.evaluate(run_pipeline_decision, max_concurrency=1))
    report.print()
