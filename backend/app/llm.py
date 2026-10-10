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
