import json
import logging
import neatlogs
from typing import Dict, Any, List, Optional
from app.config import get_settings
from app.llm import get_litellm_client, extract_json
from app.agent.dag import SalesDAGExecutionEngine
from app.tools.cfo import get_cfo_financial_context

logger = logging.getLogger(__name__)


@neatlogs.span(kind="WORKFLOW", name="agent-conversational-orchestrator")
def run_agent_turn(
    user_message: str,
    deal_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Autonomous sales planning agent loop:
    Parses user deal instruction, extracts context, decides which deliverables
    (if any) to generate immediately, dispatches tools via the DAG Engine,
    and returns conversational responses with proactive follow-up recommendations.
    """
    settings = get_settings()
    llm_client = get_litellm_client()
    llm_model = settings.litellm_model or "nova-pro"

    context = deal_context or {}
    account_name = context.get("account_name", "Enterprise Account")
    deal_size = context.get("deal_size", "$150,000 ARR")
    competitor = context.get("competitor", "LegacyVendor")
    recipient = context.get("recipient", "Buyer Sponsor")

    intent_system = """You are the BUST AI Agent Orchestrator — an elite enterprise revenue copilot.
Your job is to analyze the user's sales instruction, update deal context, selectively decide which deliverables to generate, formulate an executive strategic answer, and ask proactive follow-up questions recommending complementary assets.

Available Deliverables:
- "create_battlecards": Objection handling & competitor talk-tracks.
- "create_presentation": 4-5 slide executive pitch deck (16:9 widescreen).
- "create_flowchart": 6-stage Mutual Action Plan (MAP) closing roadmap.
- "create_email": Executive proposal follow-up email.
- "publish_suite": Private buyer deal room with encrypted digital keycard.

Decision Rules:
1. ONLY set a deliverable flag to true if the user explicitly requested it (e.g. "make battlecards", "create pitch deck", "draft email", "make presentations", "generate all", etc.).
2. If the user shares raw meeting notes, discovery details, or asks general strategy questions without asking to generate specific collateral:
   - Set all deliverable flags to false.
   - In "explanation", summarize key deal risks and recommend what they should build first.
3. If deliverables ARE generated:
   - In "explanation", explain what was created and suggest what companion assets they need next to close the deal.
4. Always provide "follow_ups": an array of 2 to 4 recommended next action objects:
   [
     {"label": "📊 Executive Pitch Deck", "prompt": "Create an executive pitch deck for this deal."},
     {"label": "🎴 Objection Battlecards", "prompt": "Generate competitive objection battlecards with talk-tracks."},
     {"label": "🗺️ Mutual Action Plan", "prompt": "Build a 6-stage Mutual Action Plan closing roadmap."},
     {"label": "✉️ Proposal Email", "prompt": "Draft an executive follow-up proposal email."}
   ]

Return strictly valid JSON adhering to this schema:
{
  "create_battlecards": false,
  "create_presentation": false,
  "create_flowchart": false,
  "create_email": false,
  "publish_suite": false,
  "account_name": "...",
  "deal_size": "...",
  "competitor": "...",
  "recipient": "...",
  "explanation": "...",
  "follow_ups": [
    {"label": "...", "prompt": "..."}
  ]
}
"""

    user_query = f"Current Deal Context: Account='{account_name}', Size='{deal_size}', Competitor='{competitor}', Recipient='{recipient}'\nUser Instruction: {user_message}"

    try:
        completion = llm_client.chat.completions.create(
            model=llm_model,
            messages=[
                {"role": "system", "content": intent_system},
                {"role": "user", "content": user_query},
            ],
            temperature=0.1,
        )
        plan = extract_json(completion.choices[0].message.content or "")
    except Exception as e:
        logger.warning(f"Fallback intent parsing: {e}")
        # Detect simple keywords in user message
        msg_lower = user_message.lower()
        wants_bc = any(k in msg_lower for k in ["battlecard", "card", "objection"])
        wants_deck = any(k in msg_lower for k in ["deck", "presentation", "slide", "pitch", "ppt"])
        wants_email = any(k in msg_lower for k in ["email", "followup", "follow-up", "outreach"])
        wants_map = any(k in msg_lower for k in ["map", "roadmap", "plan", "flowchart"])
        wants_suite = any(k in msg_lower for k in ["suite", "room", "keycard"])
        wants_all = any(k in msg_lower for k in ["all", "everything", "complete"])

        if wants_all:
            wants_bc = wants_deck = wants_email = wants_map = wants_suite = True

        plan = {
            "create_battlecards": wants_bc,
            "create_presentation": wants_deck,
            "create_flowchart": wants_map,
            "create_email": wants_email,
            "publish_suite": wants_suite,
            "account_name": account_name,
            "deal_size": deal_size,
            "competitor": competitor,
            "recipient": recipient,
            "explanation": f"Reviewed deal context for {account_name}. Ready to synthesize enterprise sales collateral.",
            "follow_ups": [
                {"label": "📊 Executive Pitch Deck", "prompt": f"Generate a 5-slide executive presentation for {account_name}."},
                {"label": "🎴 Objection Battlecards", "prompt": f"Create competitive objection battlecards for {account_name} vs {competitor}."},
                {"label": "🗺️ Mutual Action Plan", "prompt": f"Build a 6-stage Mutual Action Plan closing roadmap for {account_name}."},
                {"label": "✉️ Proposal Email", "prompt": f"Draft an executive proposal follow-up email for {account_name}."},
            ],
        }

    account_name = plan.get("account_name") or account_name
    deal_size = plan.get("deal_size") or deal_size
    competitor = plan.get("competitor") or competitor
    recipient = plan.get("recipient") or recipient

    active_context = {
        "account_name": account_name,
        "deal_size": deal_size,
        "competitor": competitor,
        "recipient": recipient,
    }

    # Fetch financial modeling context from cfo.ai tool
    cfo_context = get_cfo_financial_context(account_name=account_name, deal_size=deal_size)
    active_context["cfo_metrics"] = cfo_context

    # Execute via DAG Engine only if at least one deliverable is flagged
    dag_engine = SalesDAGExecutionEngine(deal_context=active_context, user_instruction=user_message)
    dag_engine.build_plan(plan)
    dag_result = dag_engine.run()

    actions_taken = [
        dag_engine.nodes[nid].tool_name
        for nid in dag_result["completed_nodes"]
        if nid in dag_engine.nodes
    ]

    # Dynamically tailor follow-ups based on what was just created
    default_follow_ups = [
        {"label": "📊 Executive Pitch Deck", "prompt": f"Create an executive presentation deck for {account_name} ({deal_size})."},
        {"label": "🎴 Objection Battlecards", "prompt": f"Generate competitive objection battlecards for {account_name} vs {competitor}."},
        {"label": "🗺️ Mutual Action Plan", "prompt": f"Build a 6-stage Mutual Action Plan closing roadmap for {account_name}."},
        {"label": "✉️ Proposal Email", "prompt": f"Draft an executive proposal follow-up email for {recipient} at {account_name}."},
        {"label": "🏨 Buyer Deal Room", "prompt": f"Issue an encrypted digital keycard buyer suite for {account_name}."},
    ]

    raw_follow_ups = plan.get("follow_ups") or default_follow_ups
    # Filter out deliverables that were just generated in this turn
    filtered_follow_ups = []
    for fu in raw_follow_ups:
        lbl = fu.get("label", "").lower()
        if "battlecard" in lbl and "create_battlecards" in actions_taken:
            continue
        if ("deck" in lbl or "presentation" in lbl or "ppt" in lbl) and "create_presentation" in actions_taken:
            continue
        if ("email" in lbl or "proposal" in lbl) and "create_email" in actions_taken:
            continue
        if ("map" in lbl or "roadmap" in lbl or "action plan" in lbl) and "create_flowchart" in actions_taken:
            continue
        if ("room" in lbl or "suite" in lbl or "keycard" in lbl) and "publish_suite" in actions_taken:
            continue
        filtered_follow_ups.append(fu)

    if not filtered_follow_ups:
        filtered_follow_ups = [
            {"label": "🏨 Buyer Deal Room", "prompt": f"Publish a private buyer deal room suite for {account_name}."},
            {"label": "⚡ Full Deal Review", "prompt": f"Run a complete deal execution check for {account_name}."}
        ]

    explanation = plan.get("explanation")
    if not explanation:
        if actions_taken:
            explanation = f"Generated {len(actions_taken)} sales assets for **{account_name}** ({deal_size}). Previews are ready on the side panel."
        else:
            explanation = f"Analyzed opportunity for **{account_name}** ({deal_size}). You can select which sales deliverables to prepare below."

    return {
        "status": "success",
        "agent_reply": explanation,
        "actions_taken": actions_taken,
        "artifacts": dag_result["artifacts"],
        "steps": dag_result["step_records"],
        "total_duration_ms": dag_result["total_duration_ms"],
        "deal_context": active_context,
        "follow_ups": filtered_follow_ups[:4],
    }
