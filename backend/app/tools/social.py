import json
import logging
import neatlogs
from typing import Dict, Any, Optional
from app.config import get_settings
from app.llm import get_litellm_client, extract_json
from app.services.artifact_store import save_artifact

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an elite enterprise social selling and executive intelligence graph strategist.
Your role is to map the account's buyer committee and craft high-impact touchpoints for X (Twitter) and LinkedIn to engage senior decision makers.

Given the account name, buyer persona, competitor, deal context, and financial ROI metrics:
Generate:
1. "executive_dm": A primary personalized, high-value direct message (under 350 chars) citing operational pain or verified ROI.
2. "public_hook": A public engagement quote-tweet or post reply hook.
3. "provocative_question": A sharp, thought-provoking question challenging vendor lock-in, TCO, or latency.
4. "platform": "X (Twitter) & LinkedIn"
5. "key_points": 2-3 bullet points summarizing the tactical angle.
6. "stakeholders": A structured buyer committee social graph containing 3-4 distinct personas:
   - Executive Sponsor (VP Infra/Eng)
   - Economic Buyer (CFO/VP Finance)
   - Technical Champion (Lead Architect/DevOps)
   - Security & Compliance (CISO/Head of Security)
   Each with: id, name, role, channel, handle, avatar_icon, dm, hook, influence_level ("Decision Authority", "Executive Sponsor", "Key Evaluator", "Compliance Gatekeeper").
7. "graph_edges": Array of connecting influence relationships (e.g. [{"source": "account", "target": "sponsor", "relation": "Executive Decision Maker"}]).

You MUST return strictly valid JSON matching this schema:
{
  "account_name": "<Account Name>",
  "recipient": "<Executive Name / Persona>",
  "platform": "X (Twitter) & LinkedIn",
  "executive_dm": "...",
  "public_hook": "...",
  "provocative_question": "...",
  "key_points": ["...", "..."],
  "stakeholders": [
    {
      "id": "sponsor",
      "name": "Alex Rivera",
      "role": "VP of Infrastructure",
      "channel": "X / Twitter DM",
      "handle": "@alex_infra",
      "avatar_icon": "⚡",
      "dm": "...",
      "hook": "...",
      "influence_level": "Executive Sponsor"
    },
    {
      "id": "cfo",
      "name": "Elena Rostova",
      "role": "Chief Financial Officer",
      "channel": "LinkedIn InMail",
      "handle": "in/elena-rostova",
      "avatar_icon": "💼",
      "dm": "...",
      "hook": "...",
      "influence_level": "Decision Authority"
    },
    {
      "id": "tech_lead",
      "name": "Marcus Chen",
      "role": "Principal Architect",
      "channel": "Public X / Thread",
      "handle": "@marcus_builds",
      "avatar_icon": "🛠️",
      "dm": "...",
      "hook": "...",
      "influence_level": "Key Evaluator"
    }
  ],
  "graph_edges": [
    {"source": "account", "target": "sponsor", "relation": "Direct Leadership"},
    {"source": "account", "target": "cfo", "relation": "Budget Sign-off"},
    {"source": "account", "target": "tech_lead", "relation": "Architecture Review"},
    {"source": "tech_lead", "target": "sponsor", "relation": "Technical Buy-in"},
    {"source": "sponsor", "target": "cfo", "relation": "Capital Allocation Request"}
  ]
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
    """Generate structured executive social graph and touchpoints and save to SQLite."""
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
        logger.warning(f"Fallback social graph generation: {e}")
        parsed = {}

    # Normalize and ensure stakeholders social graph exists
    if not parsed or not isinstance(parsed, dict):
        parsed = {}

    parsed.setdefault("account_name", account_name)
    parsed.setdefault("recipient", recipient)
    parsed.setdefault("platform", "X (Twitter) & LinkedIn")
    parsed.setdefault(
        "executive_dm",
        f"Hi {recipient}, saw {account_name}'s recent push. Many teams evaluating {competitor or 'legacy stacks'} are finding fast payback and zero downtime by decoupling workflows. Worth a 5-min chat next week?",
    )
    parsed.setdefault(
        "public_hook",
        f"Decoupling enterprise architecture is the fastest path to reducing lock-in. Great to see teams like {account_name} prioritizing efficiency over legacy vendor bloat.",
    )
    parsed.setdefault(
        "provocative_question",
        f"How much of {account_name}'s infrastructure budget is currently tied to legacy maintenance vs proactive feature velocity?",
    )
    parsed.setdefault("key_points", ["Highlight vendor lock-in", "Anchor on fast payback"])

    if not parsed.get("stakeholders"):
        parsed["stakeholders"] = [
            {
                "id": "sponsor",
                "name": f"{recipient} (Lead)",
                "role": "Executive Sponsor",
                "channel": "X / Twitter DM",
                "handle": f"@{account_name.lower()}_lead",
                "avatar_icon": "⚡",
                "dm": parsed["executive_dm"],
                "hook": parsed["public_hook"],
                "influence_level": "Executive Sponsor",
            },
            {
                "id": "cfo",
                "name": "Finance Committee",
                "role": "Economic Buyer",
                "channel": "LinkedIn InMail",
                "handle": "in/finance-committee",
                "avatar_icon": "💼",
                "dm": f"Re: {account_name} ROI modeling. Our commercial metrics show < 210-day break-even and validated annual savings. Happy to share our 1-page financial impact brief.",
                "hook": f"Capital efficiency in enterprise SaaS is no longer optional. How {account_name} is evaluating vendor payback periods.",
                "influence_level": "Decision Authority",
            },
            {
                "id": "tech_lead",
                "name": "Lead Architect",
                "role": "Technical Champion",
                "channel": "Public X / Thread",
                "handle": f"@{account_name.lower()}_eng",
                "avatar_icon": "🛠️",
                "dm": f"Saw your work on {account_name}'s infra. We solved migration downtime with zero data loss cutover. Would love to compare technical benchmarks.",
                "hook": f"Migration downtime is usually an architectural choice, not an inevitability. How modern teams cut cutover risk by 80%.",
                "influence_level": "Key Evaluator",
            },
        ]

    if not parsed.get("graph_edges"):
        parsed["graph_edges"] = [
            {"source": "account", "target": "sponsor", "relation": "Executive Decision Maker"},
            {"source": "account", "target": "cfo", "relation": "Budget Sign-off"},
            {"source": "account", "target": "tech_lead", "relation": "Architecture Review"},
            {"source": "tech_lead", "target": "sponsor", "relation": "Technical Buy-in"},
            {"source": "sponsor", "target": "cfo", "relation": "Capital Allocation Request"},
        ]

    envelope = {
        "type": "social",
        "title": f"Executive Social Graph — {account_name}",
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
