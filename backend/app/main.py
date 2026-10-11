import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import neatlogs
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agent.orchestrator import run_agent_turn
from app.config import get_settings
from app.llm import test_completion
from app.schemas.battlecards import CreateBattlecardsRequest
from app.services.artifact_store import (
    clear_all_artifacts,
    get_artifact,
    get_by_share_id,
    list_artifacts,
    publish_artifact,
    save_artifact,
)
from app.tools.battlecards import create_battlecards

logger = logging.getLogger("bust-backend")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    api_key = settings.neatlogs_api_key
    if api_key:
        logger.info("Initializing NeatLogs SDK...")
        neatlogs.init(
            api_key=api_key,
            endpoint="https://ingest.neatlogs.com",
            workflow_name="llm-completion",
        )
    yield
    if api_key:
        logger.info("Flushing and shutting down NeatLogs SDK...")
        neatlogs.flush()
        neatlogs.shutdown()


app = FastAPI(
    title="BUST Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for Astro frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TestLLMRequest(BaseModel):
    prompt: Optional[str] = "Say hello in one short sentence."
    model: Optional[str] = None


class AgentChatRequest(BaseModel):
    message: str
    deal_context: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, str]]] = None


@app.get("/health")
@app.get("/api/health")
def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "BUST Backend",
    }


@app.post("/api/agent/chat")
@app.post("/api/agent/run")
@neatlogs.span(kind="WORKFLOW", name="deal-agent-chat-turn")
def agent_chat_endpoint(req: AgentChatRequest) -> Dict[str, Any]:
    """
    Conversational Agent Endpoint:
    Directs the AI sales agent to execute tools, plan deliverables,
    and return live structured artifacts and explanations.
    """
    try:
        result = run_agent_turn(
            user_message=req.message,
            deal_context=req.deal_context,
            history=req.history,
        )
        return result
    except Exception as exc:
        logger.error(f"Error in agent chat turn: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/test-llm")
@neatlogs.span(kind="WORKFLOW")
def test_llm(req: Optional[TestLLMRequest] = None) -> Dict[str, Any]:
    """
    Test endpoint: makes a short model request to LiteLLM gateway and returns response.
    Instrumented automatically by NeatLogs.
    """
    settings = get_settings()
    if not settings.litellm_api_key:
        raise HTTPException(
            status_code=400,
            detail=(
                "LITELLM_API_KEY is not configured in backend/.env. "
                "Please configure LITELLM_API_KEY and LITELLM_MODEL to execute LLM requests."
            ),
        )

    prompt = req.prompt if req and req.prompt else "Say hello in one short sentence."
    model = req.model if req and req.model else settings.litellm_model

    try:
        result = test_completion(prompt=prompt, model=model)
        return result
    except Exception as exc:
        logger.error(f"Error calling LiteLLM: {exc}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=f"LiteLLM Gateway Error: {str(exc)}",
        )


# ==========================================
# Milestone 2: Objection Battlecards Endpoints
# ==========================================


@app.post("/api/artifacts/battlecards")
@neatlogs.span(kind="WORKFLOW", name="generate-battlecards-workflow")
def generate_battlecards_endpoint(req: CreateBattlecardsRequest) -> Dict[str, Any]:
    """
    Generates structured competitive objection battlecards from account notes.
    Persists to JSON artifact store and returns complete deliverable envelope.
    """
    try:
        artifact = create_battlecards(
            account_name=req.account_name,
            notes=req.notes,
            competitor=req.competitor or "",
            deal_size=req.deal_size or "",
        )
        return {
            "status": "success",
            "artifact": artifact,
        }
    except Exception as exc:
        logger.error(f"Failed to generate battlecards: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate battlecards: {str(exc)}",
        )


@app.get("/api/artifacts")
def get_all_artifacts() -> List[Dict[str, Any]]:
    """List all stored deal collateral artifacts."""
    return list_artifacts()


@app.get("/api/artifacts/{artifact_id}")
def get_single_artifact(artifact_id: str) -> Dict[str, Any]:
    """Retrieve an artifact by ID."""
    artifact = get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@app.post("/api/reset")
def reset_artifacts_endpoint() -> Dict[str, Any]:
    """Clears all stored artifacts from SQLite for a fresh demo."""
    deleted_count = clear_all_artifacts()
    logger.info(f"Cleared {deleted_count} artifacts from SQLite store.")
    return {
        "status": "success",
        "message": "All artifacts cleared. Ready for fresh demo.",
        "deleted_count": deleted_count,
    }


# ==========================================
# Milestone 3: Buyer Deal Rooms & Sharing Endpoints
# ==========================================


@app.post("/api/artifacts/{artifact_id}/publish")
@neatlogs.span(kind="WORKFLOW", name="publish-deal-suite")
def publish_artifact_endpoint(artifact_id: str) -> Dict[str, Any]:
    """
    Publishes an artifact and generates a secure guest digital keycard share ID.
    """
    published = publish_artifact(artifact_id)
    if not published:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {
        "status": "published",
        "share_id": published.get("share_id"),
        "artifact": published,
    }


@app.get("/api/public/suites/{share_id}")
def get_public_suite_endpoint(share_id: str) -> Dict[str, Any]:
    """
    Unauthenticated public guest endpoint: returns read-only deal suite collateral
    matching the provided digital keycard token.
    """
    suite = get_by_share_id(share_id)
    if not suite:
        raise HTTPException(
            status_code=404,
            detail="Deal Suite not found or keycard access has expired.",
        )
    return {
        "status": "active",
        "suite_keycard": share_id,
        "deal_context": suite.get("deal_context", {}),
        "title": suite.get("title", ""),
        "type": suite.get("type", ""),
        "content": suite.get("content", {}),
        "updated_at": suite.get("updated_at", ""),
    }
