import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

import neatlogs
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import get_settings
from app.llm import test_completion

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


@app.get("/health")
def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "BUST Backend",
    }


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
