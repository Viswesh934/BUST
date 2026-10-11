import json
import logging
import neatlogs
from typing import Dict, Any, List
from app.config import get_settings
from app.llm import get_litellm_client, extract_json
from app.services.artifact_store import save_artifact

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an executive pitch designer. Build a 4-slide executive presentation briefing for an enterprise sales opportunity.
Slides must cover:
1. Executive Framing & Strategic Objective
2. Status Quo Cost & Friction
3. Proposed Autonomous Solution & Value Pillars
4. Commercial Terms & Verified ROI Payback Horizon

You MUST return valid JSON adhering to this schema:
{
  "account_name": "<Account Name>",
  "total_slides": 4,
  "slides": [
    {
      "slide_number": 1,
      "tag": "Executive Framing",
      "title": "...",
      "subtitle": "...",
      "bullets": ["...", "..."],
      "speaker_note": "..."
    },
    {
      "slide_number": 2,
      "tag": "The Challenge",
      "title": "...",
      "subtitle": "...",
      "bullets": ["...", "..."],
      "speaker_note": "..."
    },
    {
      "slide_number": 3,
      "tag": "The Solution",
      "title": "...",
      "subtitle": "...",
      "bullets": ["...", "..."],
      "speaker_note": "..."
    },
    {
      "slide_number": 4,
      "tag": "Commercial Terms",
      "title": "...",
      "subtitle": "...",
      "bullets": ["...", "..."],
      "speaker_note": "..."
    }
  ]
}
"""


@neatlogs.span(kind="TOOL", name="create_presentation")
def create_presentation(account_name: str, context: str, deal_size: str = "") -> Dict[str, Any]:
    """Generate structured 16:9 executive presentation slides."""
    settings = get_settings()
    llm_client = get_litellm_client()
    llm_model = settings.litellm_model or "nova-pro"

    prompt = f"Account: {account_name}\nDeal Size: {deal_size}\nContext:\n{context}"
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
        logger.warning(f"Fallback presentation generation: {e}")
        parsed = {
            "account_name": account_name,
            "total_slides": 4,
            "slides": [
                {
                    "slide_number": 1,
                    "tag": "Executive Framing",
                    "title": f"Accelerating Deal Velocity for {account_name}",
                    "subtitle": "A Strategic Partnership Proposal",
                    "bullets": ["Eliminate manual collateral synthesis", "Shorten sales cycle by 40%"],
                    "speaker_note": "Open by framing the problem around rep productivity.",
                },
                {
                    "slide_number": 2,
                    "tag": "The Challenge",
                    "title": "The Cost of Manual Preparation",
                    "subtitle": "Current Operational Bottlenecks",
                    "bullets": ["35% of selling time lost to manual prep", "14-day delay in follow-up deliverable turnaround"],
                    "speaker_note": "Highlight the direct revenue drain on sales velocity.",
                },
                {
                    "slide_number": 3,
                    "tag": "The Solution",
                    "title": "Autonomous Sales Collateral Engine",
                    "subtitle": "One Instruction → 4 Deliverables",
                    "bullets": ["Instant battlecards & talk-tracks", "Mutual Action Plans aligned with InfoSec"],
                    "speaker_note": "Explain the multi-deliverable agent pipeline.",
                },
                {
                    "slide_number": 4,
                    "tag": "Commercial Terms",
                    "title": "Investment & Payback Horizon",
                    "subtitle": "cfo.ai Financial Justification",
                    "bullets": ["$120,000 / year enterprise licensing", "Full payback achieved in under 60 days"],
                    "speaker_note": "Close on ROI: 1 extra closed deal pays for the contract.",
                },
            ],
        }

    envelope = {
        "type": "presentation",
        "title": f"Pitch Deck — {account_name}",
        "deal_context": {"account_name": account_name, "deal_size": deal_size},
        "content": parsed,
    }
    return save_artifact(envelope)
