"""Vector Memory Vault — ChromaDB-backed short-term and long-term memory.

Short-term: session-scoped breadcrumb trail (plan_id keyed).
Long-term:  persistent cross-session facts, user preferences, domain knowledge.
Privacy:    wipe_session() clears short-term; wipe_all() nukes everything.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    _CHROMA_AVAILABLE = True
except ImportError:
    _CHROMA_AVAILABLE = False

from ..config import settings

logger = logging.getLogger(__name__)

_SHORT_TERM_COLLECTION = "amsab_short_term"
_LONG_TERM_COLLECTION = "amsab_long_term"


class MemoryVault:
    """Manages short-term (session) and long-term (persistent) vector memory."""

    def __init__(self) -> None:
        if not _CHROMA_AVAILABLE:
            logger.warning("ChromaDB not installed — memory vault is disabled.")
            self._client = None
            return

        self._client = chromadb.PersistentClient(
            path=settings.chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._short = self._client.get_or_create_collection(_SHORT_TERM_COLLECTION)
        self._long = self._client.get_or_create_collection(_LONG_TERM_COLLECTION)
        logger.info("MemoryVault initialised at %s", settings.chroma_path)

    def _enabled(self) -> bool:
        return self._client is not None

    # ------------------------------------------------------------------ #
    # Short-term helpers (session breadcrumbs)
    # ------------------------------------------------------------------ #

    def add_step(
        self,
        plan_id: str,
        node_id: int,
        task: str,
        output: str,
        tool: str,
    ) -> None:
        """Record a completed node execution as a breadcrumb."""
        if not self._enabled():
            return
        doc_id = f"{plan_id}__node{node_id}"
        self._short.upsert(
            ids=[doc_id],
            documents=[f"Task: {task}\nTool: {tool}\nOutput: {output[:500]}"],
            metadatas=[{
                "plan_id": plan_id,
                "node_id": node_id,
                "tool": tool,
                "ts": datetime.now(timezone.utc).isoformat(),
            }],
        )

    def get_session_breadcrumbs(self, plan_id: str) -> list[dict[str, Any]]:
        """Return ordered breadcrumbs for a session."""
        if not self._enabled():
            return []
        results = self._short.get(
            where={"plan_id": plan_id},
            include=["documents", "metadatas"],
        )
        items = []
        for doc, meta in zip(results["documents"], results["metadatas"]):
            items.append({"document": doc, **meta})
        items.sort(key=lambda x: x.get("node_id", 0))
        return items

    def wipe_session(self, plan_id: str) -> int:
        """Delete all short-term entries for a plan session."""
        if not self._enabled():
            return 0
        existing = self._short.get(where={"plan_id": plan_id})
        ids = existing["ids"]
        if ids:
            self._short.delete(ids=ids)  # safe: non-empty ids list
        logger.info("Wiped %d short-term memories for plan %s", len(ids), plan_id)
        return len(ids)

    # ------------------------------------------------------------------ #
    # Long-term helpers (user prefs, domain facts)
    # ------------------------------------------------------------------ #

    def remember(self, key: str, value: str, category: str = "general") -> None:
        """Store a long-term fact (upsert by key hash)."""
        if not self._enabled():
            return
        doc_id = hashlib.md5(key.encode()).hexdigest()
        self._long.upsert(
            ids=[doc_id],
            documents=[f"{key}: {value}"],
            metadatas=[{"key": key, "category": category, "ts": datetime.now(timezone.utc).isoformat()}],
        )

    def recall(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Semantic search across long-term memory."""
        if not self._enabled():
            return []
        try:
            results = self._long.query(
                query_texts=[query],
                n_results=min(n_results, max(1, self._long.count())),
                include=["documents", "metadatas", "distances"],
            )
            items = []
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                items.append({"document": doc, "distance": dist, **meta})
            return items
        except Exception as exc:
            logger.warning("recall error: %s", exc)
            return []

    def wipe_all_memory(self) -> None:
        """Nuclear option — clears ALL short and long-term memory."""
        if not self._enabled():
            return
        # ChromaDB requires delete_collection + recreate (can't delete with empty where)
        self._client.delete_collection(_SHORT_TERM_COLLECTION)
        self._client.delete_collection(_LONG_TERM_COLLECTION)
        self._short = self._client.get_or_create_collection(_SHORT_TERM_COLLECTION)
        self._long = self._client.get_or_create_collection(_LONG_TERM_COLLECTION)
        logger.warning("ALL MemoryVault data wiped.")

    def stats(self) -> dict[str, int]:
        """Return memory entry counts for the UI heatmap widget."""
        if not self._enabled():
            return {"short_term": 0, "long_term": 0}
        return {
            "short_term": self._short.count(),
            "long_term": self._long.count(),
        }


# Singleton — imported across the app
memory_vault = MemoryVault()
