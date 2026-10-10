import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "artifacts"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _get_file_path(artifact_id: str) -> Path:
    # Sanitize ID to prevent path traversal
    safe_id = re.sub(r"[^a-zA-Z0-9_\-]", "", artifact_id)
    return STORAGE_DIR / f"{safe_id}.json"


def save_artifact(artifact: dict) -> dict:
    """Save or create a new artifact JSON file."""
    artifact_id = artifact.get("id")
    if not artifact_id:
        random_suffix = secrets.token_hex(4)
        artifact_id = f"art_{random_suffix}"
        artifact["id"] = artifact_id

    now = datetime.now(timezone.utc).isoformat()
    if "created_at" not in artifact:
        artifact["created_at"] = now
    artifact["updated_at"] = now

    file_path = _get_file_path(artifact_id)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, ensure_ascii=False)

    return artifact


def get_artifact(artifact_id: str) -> Optional[dict]:
    """Retrieve an artifact by its unique ID."""
    file_path = _get_file_path(artifact_id)
    if not file_path.exists():
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def list_artifacts() -> List[dict]:
    """List all stored artifacts, sorted by updated_at descending."""
    artifacts = []
    for file_path in STORAGE_DIR.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                artifacts.append(json.load(f))
        except Exception:
            continue
    artifacts.sort(key=lambda a: a.get("updated_at", ""), reverse=True)
    return artifacts


def update_artifact(artifact_id: str, patch: dict) -> Optional[dict]:
    """Update an existing artifact with partial dictionary."""
    existing = get_artifact(artifact_id)
    if not existing:
        return None

    existing.update(patch)
    existing["updated_at"] = datetime.now(timezone.utc).isoformat()
    return save_artifact(existing)


def publish_artifact(artifact_id: str) -> Optional[dict]:
    """Publish an artifact and generate a public hotel suite share keycard."""
    existing = get_artifact(artifact_id)
    if not existing:
        return None

    if not existing.get("share_id"):
        account = existing.get("deal_context", {}).get("account_name", "deal")
        slug = re.sub(r"[^a-zA-Z0-9]", "", account.lower())[:8] or "deal"
        token = secrets.token_hex(3)
        existing["share_id"] = f"suite_{slug}_{token}"

    existing["is_published"] = True
    existing["updated_at"] = datetime.now(timezone.utc).isoformat()
    return save_artifact(existing)


def get_by_share_id(share_id: str) -> Optional[dict]:
    """Retrieve a published artifact by its public share keycard."""
    for file_path in STORAGE_DIR.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("share_id") == share_id and data.get("is_published"):
                    return data
        except Exception:
            continue
    return None
