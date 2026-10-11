import json
import re
from typing import Any, Dict, List, Optional
import neatlogs
from openai import OpenAI
from app.config import get_settings


def get_litellm_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> OpenAI:
    """
    Returns an OpenAI client configured for the LiteLLM OpenAI-compatible gateway,
    instrumented with Neatlogs.
    """
    settings = get_settings()
    key = api_key or settings.litellm_api_key or "dummy-key"
    url = base_url or settings.litellm_base_url
    client = OpenAI(
        api_key=key,
        base_url=url,
    )
    return neatlogs.wrap(client)


def extract_json(text: str) -> Dict[str, Any]:
    """
    Extracts and parses a JSON object from raw LLM text, safely handling
    markdown backticks, conversational preamble, and conversational postamble.
    """
    if not text:
        return {}
    clean = text.strip()
    # 1. Direct parse attempt
    try:
        return json.loads(clean)
    except Exception:
        pass

    # 2. Match markdown code block ```json ... ``` or ``` ... ```
    fence_pattern = r"```(?:json)?\s*(\{[\s\S]*?\})\s*```"
    match = re.search(fence_pattern, clean)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # 3. Find first { and matching last }
    first_idx = clean.find("{")
    last_idx = clean.rfind("}")
    if first_idx != -1 and last_idx != -1 and last_idx > first_idx:
        try:
            return json.loads(clean[first_idx : last_idx + 1])
        except Exception:
            pass

    return {}


def test_completion(
    prompt: str = "Say hello in one short sentence.",
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Sends a single test completion to the LiteLLM gateway and returns structured output.
    """
    settings = get_settings()
    selected_model = model or settings.litellm_model or "gpt-4o-mini"

    client = get_litellm_client()
    response = client.chat.completions.create(
        model=selected_model,
        messages=[
            {"role": "user", "content": prompt},
        ],
        max_tokens=60,
    )

    content = response.choices[0].message.content if response.choices else ""
    return {
        "status": "success",
        "model": selected_model,
        "response": content,
        "raw": response.model_dump() if hasattr(response, "model_dump") else str(response),
    }
