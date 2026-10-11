import json
import logging
import neatlogs
from typing import Dict, Any, Optional
from app.config import get_settings
from app.llm import get_litellm_client, extract_json
from app.services.artifact_store import save_artifact

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an elite enterprise social selling and executive outreach strategist.
Your role is to craft high-impact, non-spammy executive touchpoints for X (Twitter) and LinkedIn to engage senior decision makers.

Given the account name, buyer sponsor/persona, competitor, deal context, and financial ROI metrics:
Generate:
1. "executive_dm": A personalized, high-value direct message (under 350 characters) that respects their time, anchors on a specific operational pain or verified ROI metric, and asks a low-friction question.
2. "public_hook": A public engagement angle (quote-tweet or post reply hook) that comments constructively on their industry challenge or company milestone without being salesy.
3. "provocative_question": A sharp, thought-provoking question that challenges the status quo (e.g. regarding vendor lock-in, latency, or TCO).
4. "platform": "X (Twitter) & LinkedIn"
5. "key_points": 2-3 bullet points summarizing the tactical angle.

You MUST return strictly valid JSON matching this schema:
{
  "account_name": "<Account Name>",
  "recipient": "<Executive Name / Persona>",
  "platform": "X (Twitter) & LinkedIn",
  "executive_dm": "...",
  "public_hook": "...",
  "provocative_question": "...",
  "key_points": ["...", "..."]
}
"""


@neatlogs.span(kind="TOOL", name="create_social_touchpoint")
def create_social_touchpoint(
    account_name: str,
    recipient: str = "Executive Sponsor",
    competitor: str = "",
    context: str = "",
    deal_size: str = "",
) -> Dict[str, Any]:
    """Generate structured executive social selling touchpoints and save to SQLite."""
    settings = get_settings()
    llm_client = get_litellm_client()
    llm_model = settings.litellm_model or "nova-pro"

    user_prompt = f"""Account: {account_name}
Executive Persona: {recipient}
Competitor: {competitor or 'None / Status Quo'}
Deal Size: {deal_size}
Context & Notes:
{context}
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        completion = llm_client.chat.completions.create(
            model=llm_model,
            messages=messages,
            temperature=0.2,
        )
        parsed = extract_json(completion.choices[0].message.content or "")
    except Exception as e:
        logger.warning(f"Fallback social touchpoint generation: {e}")
        parsed = {
            "account_name": account_name,
            "recipient": recipient,
            "platform": "X (Twitter) & LinkedIn",
            "executive_dm": f"Hi {recipient}, saw {account_name}'s recent push. Many teams evaluating {competitor or 'legacy stacks'} are finding 60-day break-even by decoupling workflows. Worth a 5-min chat next week?",
            "public_hook": f"Decoupling enterprise architecture is the fastest path to reducing lock-in. Great to see teams like {account_name} prioritizing efficiency over legacy vendor bloat.",
            "provocative_question": f"How much of {account_name}'s infrastructure budget is currently tied to legacy maintenance vs proactive feature velocity?",
            "key_points": ["Highlight vendor lock-in", "Anchor on fast payback"],
        }

    envelope = {
        "type": "social",
        "title": f"Executive Social Touchpoint — {account_name}",
        "content": parsed,
        "deal_context": {
            "account_name": account_name,
            "recipient": recipient,
            "competitor": competitor,
            "deal_size": deal_size,
        },
    }

    saved = save_artifact(envelope)
    return saved
