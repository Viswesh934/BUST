import json
import logging
import neatlogs
import re
import uuid
from typing import Dict, Any, List, Optional
from app.config import get_settings
from app.llm import get_litellm_client, extract_json
from app.agent.dag import SalesDAGExecutionEngine
from app.tools.cfo import get_cfo_financial_context
from app.services.artifact_store import list_artifacts
from app.services.grounding import get_all_grounded_sources, ingest_grounding_source

logger = logging.getLogger(__name__)

DECISION_SYSTEM_PROMPT = """You are BUST — an elite enterprise revenue copilot and autonomous deal decision agent.
You maintain deep situational awareness across conversation turns, track deal stage and risks, evaluate existing collateral in the database, and take autonomous tactical decisions to help close high-value deals.

Available Tools to Execute:
1. "create_battlecards": Objection handling cards with winning talk-tracks, proof points, and verified ROI metrics.
2. "create_presentation": 4-slide executive pitch deck (16:9 widescreen) covering framing, cost of inaction, solution pillars, and commercial terms.
3. "create_flowchart": 6-stage Mutual Action Plan (MAP) closing roadmap with target close dates and milestone owners.
4. "create_email": High-impact executive proposal / follow-up email tailored to the economic buyer or champion.
5. "create_social": Executive touchpoint for X (Twitter) & LinkedIn (direct message hook, public angle, provocative question).
6. "publish_suite": Digital encrypted guest keycard deal room suite for enterprise stakeholders.
7. "analyze_competitor": In-depth competitor teardown, online public revenue analysis (or undisclosed/private handling), pricing traps, bake-off landmines, and deep B2B sales research powered by Crustdata (headcount growth, funding, hiring signals, and tech stack).

Decision Rules:
1. Multi-turn Memory: If user refers to previous context (e.g., "they asked about pricing", "draft the deck for them", "what should we say?"), preserve and build on the account, competitor, and objections discussed in previous turns.
2. Context Updates: Extract and update deal_stage, deal_health, key_objections, primary_risk, recipient, deal_size, and competitor.
3. Selective Tool Execution:
   - If the user explicitly asks for collateral (e.g., "make battlecards", "create deck", "draft proposal", "make social hook", "build MAP", "analyze competitor", "revenue numbers", "crustdata", "deep research", "generate all"): set that decision flag to true.
   - If the user provides new objections or competitor threats and needs collateral: synthesize a tailored battlecards briefing to counter them.
   - If the user asks about competitor intelligence, teardown, revenue, or deep sales research (Crustdata firmographics, headcount, funding, hiring signals): set "analyze_competitor" to true.
   - If the user shares raw discovery notes or asks strategy/tactical questions: analyze the deal dynamics, provide strategic advice in "strategic_reply", and suggest companion actions via "follow_ups" without triggering unwanted tools.
4. Tool Briefings: For every tool flagged true in "decisions", you MUST write a rich, tailored "tool_briefs" entry weaving the prospect's actual pains, quotes, competitor threats, and CFO metrics so the tool produces deeply personalized output.
5. Strategic Reply: Write an executive-grade advisory reply addressing the sales rep directly. Explain your strategic diagnosis of the deal, the rationale behind any decisions taken, how you mitigated key risks, and what move to make next.

Return strictly valid JSON adhering to this schema:
{
  "deal_state_updates": {
    "account_name": "<Account Name>",
    "deal_size": "<Deal ARR>",
    "deal_stage": "<Discovery | Competitive Bake-off | Technical Validation | Proposal & ROI | Contract Closing>",
    "deal_health": "<Strong | At Risk | Competitive Pressure | Early Discovery>",
    "competitor": "<Competitor Name>",
    "recipient": "<Key Sponsor Persona / Name>",
    "key_objections": ["<Objection 1>", "<Objection 2>"],
    "primary_risk": "<Biggest single risk to closing this deal>"
  },
  "decisions": {
    "create_battlecards": false,
    "create_presentation": false,
    "create_flowchart": false,
    "create_email": false,
    "create_social": false,
    "publish_suite": false,
    "analyze_competitor": false
  },
  "decision_rationale": "<1-2 sentences explaining WHY these specific moves were made>",
  "tool_briefs": {
    "battlecards_brief": null,
    "presentation_brief": null,
    "flowchart_brief": null,
    "email_brief": null,
    "social_brief": null,
    "competitor_brief": null
  },
  "strategic_reply": "<Executive advisory directly addressing the user>",
  "follow_ups": [
    {"label": "<Emoji + short label>", "prompt": "<Clear prompt action>"}
  ]
}
"""


def run_agent_turn(
    user_message: str,
    deal_context: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Autonomous sales planning agent loop:
    1. Ingests full conversation history and active deal state.
    2. Queries SQLite for existing account artifacts to avoid redundant work.
    3. Calculates live financial metrics from cfo.ai.
    4. Evaluates deal stage, risks, and autonomously decides which tools to trigger.
    5. Dispatches tools via the DAG Engine with synthesized, high-context briefings.
    6. Returns an executive-level strategic advisory response with proactive next moves.
    """
    settings = get_settings()
    llm_client = get_litellm_client()
    llm_model = settings.litellm_model or "nova-pro"

    # 1. Base Context Ingestion
    ctx = dict(deal_context or {})
    account_name = ctx.get("account_name", "Enterprise Account")
    deal_size = ctx.get("deal_size", "")
    competitor = ctx.get("competitor", "LegacyVendor")
    recipient = ctx.get("recipient", "Buyer Sponsor")
    deal_stage = ctx.get("deal_stage", "Discovery")
    deal_health = ctx.get("deal_health", "Early Discovery")
    key_objections = list(ctx.get("key_objections") or [])
    primary_risk = ctx.get("primary_risk", "")
    decision_log = list(ctx.get("decision_log") or [])

    # 2. Query Existing Collateral in SQLite
    try:
        all_artifacts = list_artifacts()
        account_artifacts = [
            a for a in all_artifacts
            if a.get("deal_context", {}).get("account_name", "").lower() == account_name.lower()
        ]
        existing_types = [a.get("type", "generic") for a in account_artifacts]
        existing_collateral_str = ", ".join(set(existing_types)) if existing_types else "None in database"
    except Exception as e:
        logger.warning(f"Failed to query existing artifacts from SQLite: {e}")
        existing_collateral_str = "None in database"

    # 3. Calculate Live CFO Financial Grounding
    cfo_context = get_cfo_financial_context(account_name=account_name, deal_size=deal_size)

    # 4. Auto-ingest URLs from user directive if present
    url_matches = re.findall(r'https?://[^\s]+', user_message)
    for u in url_matches:
        clean_u = u.rstrip(".,;:)\"'>")
        try:
            if "github.com" in clean_u:
                ingest_grounding_source("github", clean_u)
            elif clean_u.lower().endswith(".pdf"):
                ingest_grounding_source("pdf", clean_u)
            else:
                ingest_grounding_source("website", clean_u)
        except Exception as e:
            logger.warning(f"Auto-ingest URL failed: {e}")

    # Retrieve all active grounded sources
    sources = get_all_grounded_sources()
    sources_summary_list = []
    for s in sources:
        c = s.get("content") or {}
        facts = ", ".join(c.get("key_technical_facts", [])[:3])
        sources_summary_list.append(f"• {c.get('title')} ({c.get('url_or_path')}): {c.get('summary')} | Verified Facts: {facts}")
    grounding_sources_str = "\n".join(sources_summary_list) if sources_summary_list else "None attached. Ground architecture in standard enterprise specifications."

    # 5. Format Conversation History
    history_lines = []
    if history and isinstance(history, list):
        for turn in history[-8:]:
            role_label = "User" if turn.get("role") == "user" else "Assistant"
            content = (turn.get("content") or "").strip()
            history_lines.append(f"{role_label}: {content}")
    history_str = "\n".join(history_lines) if history_lines else "No prior conversation turns."

    # 6. Build Decision Engine Prompt
    user_prompt = f"""=== ACTIVE DEAL STATE ===
Account: {account_name}
Deal Size: {deal_size}
Competitor: {competitor}
Recipient / Sponsor: {recipient}
Current Stage: {deal_stage}
Deal Health: {deal_health}
Active Objections: {", ".join(key_objections) if key_objections else "None recorded yet"}
Primary Risk: {primary_risk or "None identified yet"}
Existing Collateral in Database: {existing_collateral_str}
CFO Financial Grounding: Deal ARR {cfo_context.get('deal_arr')}, Payback {cfo_context.get('payback_period_days')}, Annual Savings {cfo_context.get('annual_projected_savings')}, ROI {cfo_context.get('projected_roi')}

=== TECHNICAL GROUND TRUTH (GITHUB / DOCS / PDF) ===
{grounding_sources_str}

=== CONVERSATION HISTORY ===
{history_str}

=== LATEST USER DIRECTIVE ===
{user_message}
"""

    try:
        completion = llm_client.chat.completions.create(
            model=llm_model,
            messages=[
                {"role": "system", "content": DECISION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        plan = extract_json(completion.choices[0].message.content or "")
    except Exception as e:
        logger.warning(f"Fallback decision parsing: {e}")
        plan = {}

    # Heuristic Fallback if LLM parsing failed
    if not plan or not isinstance(plan, dict) or "decisions" not in plan:
        msg_lower = user_message.lower()
        wants_bc = any(k in msg_lower for k in ["battlecard", "card", "objection", "talk-track"])
        wants_deck = any(k in msg_lower for k in ["deck", "presentation", "slide", "pitch", "ppt"])
        wants_email = any(k in msg_lower for k in ["email", "followup", "follow-up", "outreach", "letter"])
        wants_map = any(k in msg_lower for k in ["map", "roadmap", "plan", "flowchart", "milestone"])
        wants_social = any(k in msg_lower for k in ["social", "twitter", "x", "dm", "linkedin", "touchpoint"])
        wants_suite = any(k in msg_lower for k in ["suite", "room", "keycard"])
        wants_comp = any(k in msg_lower for k in ["competitor", "competition", "teardown", "landmine", "revenue", "bake-off", "bakeoff", "versus", " vs ", "crust", "crustdata", "deep research", "firmographics", "headcount", "hiring"])
        wants_all = any(k in msg_lower for k in ["all", "everything", "complete"])

        if wants_all:
            wants_bc = wants_deck = wants_email = wants_map = wants_suite = wants_comp = True

        plan = {
            "deal_state_updates": {
                "account_name": account_name,
                "deal_size": deal_size,
                "deal_stage": "Evaluation" if (wants_bc or wants_deck) else deal_stage,
                "deal_health": deal_health,
                "competitor": competitor,
                "recipient": recipient,
                "key_objections": key_objections,
                "primary_risk": primary_risk or f"Competitive displacement by {competitor}",
            },
            "decisions": {
                "create_battlecards": wants_bc,
                "create_presentation": wants_deck,
                "create_flowchart": wants_map,
                "create_email": wants_email,
                "create_social": wants_social,
                "publish_suite": wants_suite,
                "analyze_competitor": wants_comp,
            },
            "decision_rationale": f"Directly responded to sales instruction for {account_name}.",
            "tool_briefs": {
                "battlecards_brief": f"Account: {account_name}. Notes: {user_message}. Grounding: {cfo_context.get('deal_arr')} ARR, {cfo_context.get('payback_period_days')} break-even.",
                "presentation_brief": f"Account: {account_name}. Deal size: {deal_size}. Notes: {user_message}.",
                "flowchart_brief": f"Account: {account_name}. Target close roadmap. Notes: {user_message}.",
                "email_brief": f"Account: {account_name}. To: {recipient}. Notes: {user_message}.",
                "social_brief": f"Account: {account_name}. To: {recipient}. Notes: {user_message}.",
                "competitor_brief": f"Competitor: {competitor}. Target: {account_name}. Notes: {user_message}.",
            },
            "strategic_reply": f"Assessed opportunity for **{account_name}** ({deal_size}). Formulated tactical sales collateral aligned with your objectives.",
            "follow_ups": [
                {"label": "📊 Executive Pitch Deck", "prompt": f"Generate a 4-slide executive presentation for {account_name}."},
                {"label": "🎴 Objection Battlecards", "prompt": f"Create competitive objection battlecards for {account_name} vs {competitor}."},
                {"label": "🎯 Competitor Intelligence", "prompt": f"Analyze competitive intelligence and online revenue for {competitor}."},
                {"label": "🗺️ Mutual Action Plan", "prompt": f"Build a 6-stage Mutual Action Plan closing roadmap for {account_name}."},
                {"label": "✉️ Proposal Email", "prompt": f"Draft an executive proposal follow-up email for {recipient} at {account_name}."},
            ],
        }

    # 6. Merge Deal State Updates
    state_updates = plan.get("deal_state_updates") or {}
    account_name = state_updates.get("account_name") or account_name
    deal_size = state_updates.get("deal_size") or deal_size
    competitor = state_updates.get("competitor") or competitor
    recipient = state_updates.get("recipient") or recipient
    deal_stage = state_updates.get("deal_stage") or deal_stage
    deal_health = state_updates.get("deal_health") or deal_health
    primary_risk = state_updates.get("primary_risk") or primary_risk

    new_objs = state_updates.get("key_objections") or []
    for obj in new_objs:
        if obj and obj not in key_objections:
            key_objections.append(obj)

    # Re-evaluate CFO context if deal size changed
    if deal_size != ctx.get("deal_size"):
        cfo_context = get_cfo_financial_context(account_name=account_name, deal_size=deal_size)

    active_context = {
        "account_name": account_name,
        "deal_size": deal_size,
        "competitor": competitor,
        "recipient": recipient,
        "deal_stage": deal_stage,
        "deal_health": deal_health,
        "key_objections": key_objections,
        "primary_risk": primary_risk,
        "cfo_metrics": cfo_context,
        "decision_log": decision_log,
    }

    # 7. Execute DAG Engine with Tailored Briefs
    plan_decisions = plan.get("decisions") or {}
    tool_briefs = plan.get("tool_briefs") or {}

    dag_engine = SalesDAGExecutionEngine(deal_context=active_context, user_instruction=user_message)
    dag_engine.build_plan(plan_decisions, tool_briefs=tool_briefs)
    dag_result = dag_engine.run()

    actions_taken = [
        dag_engine.nodes[nid].tool_name
        for nid in dag_result["completed_nodes"]
        if nid in dag_engine.nodes
    ]

    # Record decision in decision log
    if actions_taken:
        active_context["decision_log"].append({
            "instruction": user_message,
            "actions": actions_taken,
            "rationale": plan.get("decision_rationale") or "Autonomous collateral generation",
        })

    # 8. Filter and Refine Follow-ups
    default_follow_ups = [
        {"label": "📊 Executive Pitch Deck", "prompt": f"Create an executive presentation deck for {account_name} ({deal_size})."},
        {"label": "🎯 Competitor Intelligence", "prompt": f"Analyze competitive intelligence and online revenue for {competitor}."},
        {"label": "🔍 Crustdata Deep Research", "prompt": f"Perform deep sales research and firmographics on {competitor} using Crustdata."},
        {"label": "🎴 Objection Battlecards", "prompt": f"Generate competitive objection battlecards for {account_name} vs {competitor}."},
        {"label": "🗺️ Mutual Action Plan", "prompt": f"Build a 6-stage Mutual Action Plan closing roadmap for {account_name}."},
        {"label": "✉️ Proposal Email", "prompt": f"Draft an executive proposal follow-up email for {recipient} at {account_name}."},
        {"label": "🐦 Social Touchpoint", "prompt": f"Draft an executive outreach DM and hook for {recipient} on X/LinkedIn."},
        {"label": "🏨 Buyer Deal Room", "prompt": f"Issue an encrypted digital keycard buyer suite for {account_name}."},
    ]

    raw_follow_ups = plan.get("follow_ups") or default_follow_ups
    filtered_follow_ups = []
    for fu in raw_follow_ups:
        lbl = fu.get("label", "").lower()
        if "battlecard" in lbl and "create_battlecards" in actions_taken:
            continue
        if ("competitor" in lbl or "intelligence" in lbl or "teardown" in lbl) and "analyze_competitor" in actions_taken:
            continue
        if ("deck" in lbl or "presentation" in lbl or "ppt" in lbl) and "create_presentation" in actions_taken:
            continue
        if ("email" in lbl or "proposal" in lbl) and "create_email" in actions_taken:
            continue
        if ("map" in lbl or "roadmap" in lbl or "action plan" in lbl) and "create_flowchart" in actions_taken:
            continue
        if ("social" in lbl or "twitter" in lbl or "touchpoint" in lbl) and "create_social" in actions_taken:
            continue
        if ("room" in lbl or "suite" in lbl or "keycard" in lbl) and "publish_suite" in actions_taken:
            continue
        filtered_follow_ups.append(fu)

    if not filtered_follow_ups:
        filtered_follow_ups = [
            {"label": "🏨 Buyer Deal Room", "prompt": f"Publish a private buyer deal room suite for {account_name}."},
            {"label": "⚡ Full Deal Review", "prompt": f"Run a complete deal execution check for {account_name}."}
        ]

    # 9. Format Strategic Reply
    strategic_reply = plan.get("strategic_reply")
    if not strategic_reply:
        if actions_taken:
            strategic_reply = f"Strategically synthesized {len(actions_taken)} deal deliverables for **{account_name}** ({deal_size}). Collateral is ready for review on the side dock."
        else:
            strategic_reply = f"Analyzed opportunity for **{account_name}** ({deal_size}). Stage: **{deal_stage}** | Health: **{deal_health}**.\n\nKey Risk: {primary_risk or 'Competitive evaluation ongoing'}. Select next strategic moves below."

    return {
        "status": "success",
        "agent_reply": strategic_reply,
        "decision_rationale": plan.get("decision_rationale") or "",
        "actions_taken": actions_taken,
        "artifacts": dag_result["artifacts"],
        "steps": dag_result["step_records"],
        "total_duration_ms": dag_result["total_duration_ms"],
        "deal_context": active_context,
        "follow_ups": filtered_follow_ups[:4],
    }
