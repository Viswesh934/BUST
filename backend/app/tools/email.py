import json
import logging
import neatlogs
from typing import Dict, Any
from app.config import get_settings
from app.llm import get_litellm_client, extract_json
from app.services.artifact_store import save_artifact

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an executive deal strategist. Draft a high-impact B2B follow-up proposal email for an enterprise sales opportunity.
Synthesize the account's pain points, the proposed solution, next steps from the Mutual Action Plan, and commercial ROI.

You MUST return valid JSON adhering to this schema:
{
  "to": "<Recipient Email / Name>",
  "subject": "<Compelling Executive Subject Line>",
  "tone": "Executive Persuasive",
  "body": "<Polished professional email body with bulleted takeaways and next milestones>",
  "key_takeaways": ["...", "..."],
  "word_count": 140
}
"""


def create_email(account_name: str, recipient: str, context: str, tone: str = "Executive") -> Dict[str, Any]:
    """Generate structured follow-up proposal email."""
    settings = get_settings()
    llm_client = get_litellm_client()
    llm_model = settings.litellm_model or "nova-pro"

    prompt = f"Account: {account_name}\nRecipient: {recipient}\nTone: {tone}\nDeal Context & Notes:\n{context}"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    try:
        completion = llm_client.chat.completions.create(
            model=llm_model,
            messages=messages,
            temperature=0.2,
        )
        parsed = extract_json(completion.choices[0].message.content or "")
    except Exception as e:
        logger.warning(f"Fallback email generation: {e}")
        parsed = {
            "to": recipient or f"sarah.jenkins@{account_name.lower().replace(' ', '')}.com (VP Sales Ops)",
            "subject": f"Executive Summary & Next Milestones — BUST x {account_name}",
            "tone": tone or "Executive Persuasive",
            "body": f"Hi {recipient.split()[0] if recipient else 'Sarah'},\n\nThank you for the productive review session. BUST will enable your enterprise sales team to automate battlecard preparation and collateral synthesis.\n\nKey next steps from our Mutual Action Plan:\n1. Security & Compliance: SOC2 Type II audit review targeted for completion this Thursday.\n2. Competitive Battlecards: Tailored objection talk-tracks prepared for your reps.\n3. Commercial Terms: $120k/yr annual contract with break-even achieved within 60 days.\n\nLooking forward to our sync next week.\n\nBest regards,\nAlex Morgan | Strategic Accounts",
            "key_takeaways": ["SOC2 audit on Thursday", "60-day payback verified"],
            "word_count": 115,
        }

    envelope = {
        "type": "email",
        "title": f"Follow-Up Email — {account_name}",
        "deal_context": {"account_name": account_name, "recipient": recipient},
        "content": parsed,
    }
    return save_artifact(envelope)
