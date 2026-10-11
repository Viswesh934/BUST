import json
import logging
import neatlogs
from typing import Dict, Any, List
from app.config import get_settings
from app.llm import get_litellm_client, extract_json
from app.services.artifact_store import save_artifact

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an enterprise sales engineering and deal architect specialist.
Generate a structured 6-stage Mutual Action Plan (MAP) roadmap to guide an enterprise buyer from technical discovery to contract signature.

You MUST return valid JSON adhering to this schema:
{
  "account_name": "<Account Name>",
  "target_close_date": "<Date>",
  "progress_percent": 33,
  "stages": [
    {
      "stage_number": 1,
      "name": "Technical Discovery",
      "status": "completed",
      "target_date": "...",
      "owner": "Buyer Sponsor & AE",
      "description": "...",
      "deliverable": "..."
    },
    {
      "stage_number": 2,
      "name": "Architecture & Integration Review",
      "status": "completed",
      "target_date": "...",
      "owner": "Sales Engineering",
      "description": "...",
      "deliverable": "..."
    },
    {
      "stage_number": 3,
      "name": "Security & InfoSec Compliance",
      "status": "current",
      "target_date": "...",
      "owner": "InfoSec Board",
      "description": "...",
      "deliverable": "..."
    },
    {
      "stage_number": 4,
      "name": "Commercial & Legal Review",
      "status": "upcoming",
      "target_date": "...",
      "owner": "Legal Counsel",
      "description": "...",
      "deliverable": "..."
    },
    {
      "stage_number": 5,
      "name": "CFO & Budget Authorization",
      "status": "upcoming",
      "target_date": "...",
      "owner": "VP Finance",
      "description": "...",
      "deliverable": "..."
    },
    {
      "stage_number": 6,
      "name": "Contract Execution & Kickoff",
      "status": "upcoming",
      "target_date": "...",
      "owner": "All Stakeholders",
      "description": "...",
      "deliverable": "..."
    }
  ]
}
"""


def create_flowchart(account_name: str, notes: str, target_date: str = "") -> Dict[str, Any]:
    """Generate structured Mutual Action Plan roadmap."""
    settings = get_settings()
    llm_client = get_litellm_client()
    llm_model = settings.litellm_model or "nova-pro"

    prompt = f"Account: {account_name}\nTarget Date: {target_date or 'End of Quarter'}\nNotes: {notes}"
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
        logger.warning(f"Fallback MAP generation: {e}")
        parsed = {
            "account_name": account_name,
            "target_close_date": target_date or "Oct 28, 2026",
            "progress_percent": 33,
            "stages": [
                {
                    "stage_number": 1,
                    "name": "Technical Discovery",
                    "status": "completed",
                    "target_date": "Last Week",
                    "owner": "Buyer Sponsor & AE",
                    "description": "Scoping requirements and team seats.",
                    "deliverable": "Scope Deck",
                },
                {
                    "stage_number": 2,
                    "name": "Architecture Review",
                    "status": "completed",
                    "target_date": "Yesterday",
                    "owner": "Sales Engineering",
                    "description": "Integration and workflow boundaries verified.",
                    "deliverable": "Architecture Sign-off",
                },
                {
                    "stage_number": 3,
                    "name": "Security & Compliance",
                    "status": "current",
                    "target_date": "This Thursday",
                    "owner": "InfoSec Board",
                    "description": "SOC2 audit review and zero retention verification.",
                    "deliverable": "Security Approval",
                },
                {
                    "stage_number": 4,
                    "name": "Legal & Terms",
                    "status": "upcoming",
                    "target_date": "Next Week",
                    "owner": "Legal Counsel",
                    "description": "Commercial agreement sign-off.",
                    "deliverable": "Redline Sign-off",
                },
                {
                    "stage_number": 5,
                    "name": "CFO Sign-off",
                    "status": "upcoming",
                    "target_date": "Next Month",
                    "owner": "VP Finance",
                    "description": "Budget authorization and ROI validation.",
                    "deliverable": "Budget Approval",
                },
                {
                    "stage_number": 6,
                    "name": "Contract Signature",
                    "status": "upcoming",
                    "target_date": "Closing Day",
                    "owner": "All Stakeholders",
                    "description": "DocuSign execution & kickoff.",
                    "deliverable": "Executed Agreement",
                },
            ],
        }

    envelope = {
        "type": "flowchart",
        "title": f"Mutual Action Plan — {account_name}",
        "deal_context": {"account_name": account_name},
        "content": parsed,
    }
    return save_artifact(envelope)
