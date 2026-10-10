import json
import logging
import neatlogs
from typing import Dict, Any, List, Optional
from app.config import get_settings
from app.llm import get_litellm_client
from app.agent.dag import SalesDAGExecutionEngine

logger = logging.getLogger(__name__)


@neatlogs.span(kind="WORKFLOW", name="agent-conversational-orchestrator")
def run_agent_turn(
    user_message: str,
    deal_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Core conversational agent loop:
    Parses user request, identifies deliverables to create/update,
    dispatches tools via an autonomous DAG Execution Engine,
    records step telemetry, and returns structured outputs for inline rendering.
    """
    settings = get_settings()
    llm_client = get_litellm_client()
    llm_model = settings.litellm_model or "nova-pro"

    context = deal_context or {}
    account_name = context.get("account_name", "ACME Corp")
    deal_size = context.get("deal_size", "$150,000 ARR")
    competitor = context.get("competitor", "LegacyVendor")
    recipient = context.get("recipient", "Sarah Jenkins (VP Sales Ops)")

    # Intent analysis prompt
    intent_system = """You are the BUST AI Agent Orchestrator. The user gives you sales instructions.
Determine which tools should be executed based on the user's message:
- "create_battlecards": true/false
- "create_flowchart": true/false
- "create_email": true/false
- "create_presentation": true/false
- "publish_suite": true/false

Also extract:
- account_name (if mentioned, else keep current)
- deal_size (if mentioned, else keep current)
- competitor (if mentioned, else keep current)
- recipient (e.g. buyer contact name or email)
- explanation: brief 1-2 sentence conversational reply explaining what you generated/updated for the sales team.

Return JSON adhering to this schema:
{
  "create_battlecards": true,
  "create_flowchart": true,
  "create_email": true,
  "create_presentation": true,
  "publish_suite": true,
  "account_name": "...",
  "deal_size": "...",
  "competitor": "...",
  "recipient": "...",
  "explanation": "..."
}
"""

    user_query = f"Current Context: Account='{account_name}', Size='{deal_size}', Competitor='{competitor}'\nUser Instruction: {user_message}"
    
    try:
        completion = llm_client.chat.completions.create(
            model=llm_model,
            messages=[
                {"role": "system", "content": intent_system},
                {"role": "user", "content": user_query},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        plan = json.loads(completion.choices[0].message.content or "{}")
    except Exception as e:
        logger.warning(f"Fallback intent parsing: {e}")
        plan = {
            "create_battlecards": True,
            "create_flowchart": True,
            "create_email": True,
            "create_presentation": True,
            "publish_suite": True,
            "account_name": account_name,
            "deal_size": deal_size,
            "competitor": competitor,
            "recipient": recipient,
            "explanation": f"I've initiated the complete deal execution pipeline for {account_name}. I generated competitive battlecards against {competitor}, a 6-stage Mutual Action Plan, an executive proposal email, and issued a digital keycard for your buyer suite.",
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

    # Execute via DAG Engine
    dag_engine = SalesDAGExecutionEngine(deal_context=active_context, user_instruction=user_message)
    dag_engine.build_plan(plan)
    dag_result = dag_engine.run()

    actions_taken = [
        dag_engine.nodes[nid].tool_name
        for nid in dag_result["completed_nodes"]
        if nid in dag_engine.nodes
    ]

    return {
        "status": "success",
        "agent_reply": plan.get("explanation") or f"Executed directives for {account_name}.",
        "actions_taken": actions_taken,
        "artifacts": dag_result["artifacts"],
        "steps": dag_result["step_records"],
        "total_duration_ms": dag_result["total_duration_ms"],
        "deal_context": active_context,
    }
