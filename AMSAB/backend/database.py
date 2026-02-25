"""SQLite persistence layer for AMSAB plans and nodes."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator

from .config import settings
from .models.task_graph import NodeStatus, PlanStatus, TaskGraph
from .models.state import NodeRow, PlanRow


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.sqlite_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = _conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables on first run."""
    Path(settings.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS plans (
                plan_id     TEXT PRIMARY KEY,
                goal        TEXT NOT NULL,
                dag_json    TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'draft',
                branch_of   TEXT,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS nodes (
                plan_id      TEXT NOT NULL,
                node_id      INTEGER NOT NULL,
                status       TEXT NOT NULL DEFAULT 'pending',
                result       TEXT,
                error        TEXT,
                snapshot     TEXT,
                token_usage  INTEGER DEFAULT 0,
                started_at   TEXT,
                completed_at TEXT,
                PRIMARY KEY (plan_id, node_id),
                FOREIGN KEY (plan_id) REFERENCES plans(plan_id)
            );

            CREATE TABLE IF NOT EXISTS logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id     TEXT NOT NULL,
                node_id     INTEGER,
                level       TEXT DEFAULT 'info',
                message     TEXT NOT NULL,
                created_at  TEXT NOT NULL
            );
        """)


# ── Plan CRUD ────────────────────────────────────────────────────────────────

def create_plan(plan_id: str, goal: str, dag: TaskGraph, branch_of: str | None = None) -> None:
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO plans VALUES (?,?,?,?,?,?,?)",
            (plan_id, goal, dag.model_dump_json(), PlanStatus.draft, branch_of, now, now),
        )


def get_plan(plan_id: str) -> PlanRow | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM plans WHERE plan_id=?", (plan_id,)).fetchone()
    if not row:
        return None
    return PlanRow(
        plan_id=row["plan_id"],
        goal=row["goal"],
        dag=TaskGraph.model_validate_json(row["dag_json"]),
        status=PlanStatus(row["status"]),
        branch_of=row["branch_of"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def list_plans() -> list[PlanRow]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM plans ORDER BY created_at DESC").fetchall()
    return [
        PlanRow(
            plan_id=r["plan_id"],
            goal=r["goal"],
            dag=TaskGraph.model_validate_json(r["dag_json"]),
            status=PlanStatus(r["status"]),
            branch_of=r["branch_of"],
            created_at=datetime.fromisoformat(r["created_at"]),
            updated_at=datetime.fromisoformat(r["updated_at"]),
        )
        for r in rows
    ]


def update_plan_status(plan_id: str, status: PlanStatus, dag: TaskGraph | None = None) -> None:
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        if dag:
            conn.execute(
                "UPDATE plans SET status=?, dag_json=?, updated_at=? WHERE plan_id=?",
                (status, dag.model_dump_json(), now, plan_id),
            )
        else:
            conn.execute(
                "UPDATE plans SET status=?, updated_at=? WHERE plan_id=?",
                (status, now, plan_id),
            )


# ── Node CRUD ────────────────────────────────────────────────────────────────

def _sqlite_safe(value: Any) -> Any:
    """Convert a value to a SQLite-safe type (serialize dicts/lists, stringify enums)."""
    if isinstance(value, dict | list):
        return json.dumps(value)
    if hasattr(value, "value"):          # Enum
        return value.value
    return value


def upsert_node(plan_id: str, node_id: int, **fields: Any) -> None:
    now = datetime.utcnow().isoformat()
    # Serialize every field value so SQLite never receives a dict, list, or Enum
    safe_fields = {k: _sqlite_safe(v) for k, v in fields.items()}
    with get_db() as conn:
        existing = conn.execute(
            "SELECT 1 FROM nodes WHERE plan_id=? AND node_id=?", (plan_id, node_id)
        ).fetchone()
        if existing:
            set_clauses = ", ".join(f"{k}=?" for k in safe_fields)
            conn.execute(
                f"UPDATE nodes SET {set_clauses}, completed_at=? WHERE plan_id=? AND node_id=?",
                (*safe_fields.values(), now, plan_id, node_id),
            )
        else:
            conn.execute(
                "INSERT INTO nodes (plan_id, node_id, status, result, error, snapshot, "
                "token_usage, started_at, completed_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    plan_id, node_id,
                    _sqlite_safe(fields.get("status", NodeStatus.pending)),
                    fields.get("result"),
                    fields.get("error"),
                    json.dumps(fields.get("snapshot")) if fields.get("snapshot") else None,
                    fields.get("token_usage", 0),
                    fields.get("started_at"),
                    now,
                ),
            )


def get_node_snapshot(plan_id: str, node_id: int) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT snapshot FROM nodes WHERE plan_id=? AND node_id=?", (plan_id, node_id)
        ).fetchone()
    if row and row["snapshot"]:
        return json.loads(row["snapshot"])
    return None


# ── Logs ─────────────────────────────────────────────────────────────────────

def add_log(plan_id: str, message: str, node_id: int | None = None, level: str = "info") -> None:
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO logs (plan_id, node_id, level, message, created_at) VALUES (?,?,?,?,?)",
            (plan_id, node_id, level, message, now),
        )


def get_logs(plan_id: str, limit: int = 200) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM logs WHERE plan_id=? ORDER BY id DESC LIMIT ?", (plan_id, limit)
        ).fetchall()
    return [dict(r) for r in reversed(rows)]
