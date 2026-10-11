import json
import logging
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") or os.environ.get("LAMBDA_TASK_ROOT"):
    DB_DIR = Path("/tmp/bust_data")
else:
    DB_DIR = Path(os.environ.get("BUST_DATA_DIR", Path(__file__).resolve().parent.parent.parent / "data"))

DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "bust.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    """Initializes the SQLite schema and migrates any legacy JSON files."""
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                account_name TEXT,
                deal_size TEXT,
                competitor TEXT,
                recipient TEXT,
                is_published INTEGER DEFAULT 0,
                share_id TEXT UNIQUE,
                envelope_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_share_id ON artifacts(share_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_updated_at ON artifacts(updated_at DESC)")
        conn.commit()

    # Migrate legacy JSON files if any exist
    legacy_dir = DB_DIR / "artifacts"
    if legacy_dir.exists():
        for file_path in legacy_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and data.get("id"):
                        save_artifact(data)
                file_path.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Could not migrate legacy JSON artifact {file_path}: {e}")


# Initialize database schema immediately on import
_init_db()


def save_artifact(artifact: dict) -> dict:
    """Save or update an artifact record in the SQLite database."""
    artifact_id = artifact.get("id")
    if not artifact_id:
        random_suffix = secrets.token_hex(4)
        artifact_id = f"art_{random_suffix}"
        artifact["id"] = artifact_id

    now = datetime.now(timezone.utc).isoformat()
    if "created_at" not in artifact:
        artifact["created_at"] = now
    artifact["updated_at"] = now

    art_type = artifact.get("type", "generic")
    title = artifact.get("title", f"Artifact {artifact_id}")
    deal_context = artifact.get("deal_context") or {}
    account_name = deal_context.get("account_name", "")
    deal_size = deal_context.get("deal_size", "")
    competitor = deal_context.get("competitor", "")
    recipient = deal_context.get("recipient", "")
    is_published = 1 if artifact.get("is_published") else 0
    share_id = artifact.get("share_id")

    envelope_json = json.dumps(artifact, ensure_ascii=False)

    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO artifacts (
                id, type, title, account_name, deal_size, competitor, recipient,
                is_published, share_id, envelope_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                type = excluded.type,
                title = excluded.title,
                account_name = excluded.account_name,
                deal_size = excluded.deal_size,
                competitor = excluded.competitor,
                recipient = excluded.recipient,
                is_published = excluded.is_published,
                share_id = excluded.share_id,
                envelope_json = excluded.envelope_json,
                updated_at = excluded.updated_at
            """,
            (
                artifact_id,
                art_type,
                title,
                account_name,
                deal_size,
                competitor,
                recipient,
                is_published,
                share_id,
                envelope_json,
                artifact["created_at"],
                artifact["updated_at"],
            ),
        )
        conn.commit()

    return artifact


def get_artifact(artifact_id: str) -> Optional[dict]:
    """Retrieve an artifact by its unique ID from SQLite."""
    with _get_connection() as conn:
        row = conn.execute("SELECT envelope_json FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
        if row:
            try:
                return json.loads(row["envelope_json"])
            except Exception as e:
                logger.error(f"Failed to decode artifact JSON from SQLite: {e}")
                return None
    return None


def list_artifacts() -> List[dict]:
    """List all stored artifacts, sorted by updated_at descending."""
    results = []
    with _get_connection() as conn:
        rows = conn.execute("SELECT envelope_json FROM artifacts ORDER BY updated_at DESC").fetchall()
        for row in rows:
            try:
                results.append(json.loads(row["envelope_json"]))
            except Exception:
                continue
    return results


def update_artifact(artifact_id: str, patch: dict) -> Optional[dict]:
    """Update an existing artifact with partial dictionary."""
    existing = get_artifact(artifact_id)
    if not existing:
        return None

    existing.update(patch)
    existing["updated_at"] = datetime.now(timezone.utc).isoformat()
    return save_artifact(existing)


def publish_artifact(artifact_id: str) -> Optional[dict]:
    """Publish an artifact and generate a public hotel suite share keycard in SQLite."""
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
    """Retrieve a published artifact by its public share keycard from SQLite."""
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT envelope_json FROM artifacts WHERE share_id = ? AND is_published = 1",
            (share_id,),
        ).fetchone()
        if row:
            try:
                return json.loads(row["envelope_json"])
            except Exception:
                return None
    return None


def delete_artifact(artifact_id: str) -> bool:
    """Delete an artifact from SQLite."""
    with _get_connection() as conn:
        cursor = conn.execute("DELETE FROM artifacts WHERE id = ?", (artifact_id,))
        conn.commit()
        return cursor.rowcount > 0


def clear_all_artifacts() -> int:
    """Clear all stored artifacts from SQLite for clean demo reset."""
    with _get_connection() as conn:
        cursor = conn.execute("DELETE FROM artifacts")
        conn.commit()
        return cursor.rowcount

