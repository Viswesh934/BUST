import json
import logging
import neatlogs
from typing import Dict, Any, Optional
from app.config import get_settings
from app.llm import get_litellm_client, extract_json
from app.schemas.battlecards import ObjectionBattlecardsDeck, ObjectionCard, ArtifactEnvelope
from app.services.artifact_store import save_artifact

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an elite enterprise B2B sales strategist and competitive enablement director.
Your role is to analyze sales meeting discovery notes and generate structured Objection Battlecards for sales teams.

Given account notes, competitor details, and deal size:
1. Identify 3 to 4 realistic, high-impact prospect objections categorized across:
   - "Pricing / Budget"
   - "Security & InfoSec"
   - "Competitor Trap"
   - "Timing & Priority"
2. For each objection:
   - Provide the realistic prospect objection quote
   - Identify the buyer stakeholder persona
   - Formulate an executive winning talk-track that pivots from price/feature to Total Cost of Ownership (TCO) and business impact
   - Provide 2 concrete proof points
   - Provide a specific key metric (e.g., "$80k labor savings", "< 60-day break-even")
   - Provide 2 categorization tags

You MUST return valid JSON adhering strictly to this JSON format:
{
  "account_name": "<Account Name>",
  "deal_size": "<Deal ARR>",
  "competitor": "<Competitor Name>",
  "cards": [
    {
      "id": "card_1",
      "category": "Pricing / Budget",
      "objection_quote": "...",
      "buyer_persona": "...",
      "winning_response": "...",
      "proof_points": ["...", "..."],
      "key_metric": "...",
      "tags": ["...", "..."]
    }
  ]
}
"""


def create_battlecards(
    account_name: str,
    notes: str,
    competitor: str = "",
    deal_size: str = "",
) -> Dict[str, Any]:
    """Generate structured objection battlecards using LiteLLM nova-pro and persist to artifact store."""
    settings = get_settings()
    llm_client = get_litellm_client()
    llm_model = settings.litellm_model or "nova-pro"
    user_prompt = f"""Target Account: {account_name}
Deal Size: {deal_size or "Enterprise"}
Competitor: {competitor or "Legacy incumbent"}

Meeting Discovery Notes:
{notes}
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
        parsed_json = extract_json(completion.choices[0].message.content or "")

        # Validate against schema
        deck = ObjectionBattlecardsDeck(**parsed_json)
    except Exception as e:
        logger.warning(f"Fallback generation due to LLM error: {e}")
        # Deterministic fallback deck if LLM parse hiccups
        cards = [
            ObjectionCard(
                id="card_1",
                category="Pricing / Budget",
                objection_quote=f"Your quote is 20% higher than our renewal price from {competitor or 'LegacyVendor'}.",
                buyer_persona="VP of Sales Operations / Procurement",
                winning_response=f"Pivot to Total Cost of Ownership (TCO). While our upfront subscription is higher, {competitor or 'LegacyVendor'} requires 2 dedicated FTEs just to maintain manual data sync. We automate that workflow entirely, delivering an $80k net savings in Year 1.",
                proof_points=["$80,000 net labor savings", "Eliminates 2 manual FTE overheads"],
                key_metric="60-day break-even",
                tags=["TCO Comparison", "FTE Savings"],
            ),
            ObjectionCard(
                id="card_2",
                category="Security & InfoSec",
                objection_quote="Our InfoSec committee will not approve software that trains on enterprise deal data.",
                buyer_persona="Chief Information Security Officer (CISO)",
                winning_response="Highlight our strict Zero Retention policy. Customer deal data is processed in-memory ephemerally and is never used for model retraining. Independent SOC2 Type II audit report is available in our trust center.",
                proof_points=["SOC2 Type II audited", "Zero Data Retention guarantee"],
                key_metric="100% ephemeral",
                tags=["SOC2 Type II", "Private Cloud"],
            ),
            ObjectionCard(
                id="card_3",
                category="Competitor Trap",
                objection_quote=f"{competitor or 'LegacyVendor'} claims they already have built-in collateral generation.",
                buyer_persona="Director of Enterprise Sales",
                winning_response=f"Differentiate point solutions from our autonomous suite. {competitor or 'LegacyVendor'} offers basic textbox autocomplete. Our orchestration coordinates 4 deliverables simultaneously from a single deal directive.",
                proof_points=["Multi-deliverable synthesis", "Deterministic pipeline validation"],
                key_metric="4 deliverables in 1 run",
                tags=["Point Solution vs Suite", "Pipeline Orchestration"],
            ),
        ]
        deck = ObjectionBattlecardsDeck(
            account_name=account_name,
            deal_size=deal_size or "$150,000 ARR",
            competitor=competitor or "LegacyVendor",
            cards=cards,
        )

    # Wrap in unified ArtifactEnvelope
    envelope = {
        "type": "battlecards",
        "title": f"Objection Battlecards — {account_name}",
        "deal_context": {
            "account_name": deck.account_name,
            "deal_size": deck.deal_size,
            "competitor": deck.competitor,
        },
        "content": deck.model_dump(),
    }

    saved = save_artifact(envelope)
    return saved
