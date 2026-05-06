# ============================================
# Nexus-Graph AI Service - ChromaDB Client
# ============================================

from __future__ import annotations

from typing import Optional

import chromadb

from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger("nexus-ai.chromadb")

COLLECTION_NAME = "nexus_memory"


class ChromaDBClient:
    def __init__(self):
        self._client: Optional[chromadb.HttpClient] = None

    async def connect(self) -> None:
        s = get_settings()
        self._client = chromadb.HttpClient(host=s.chroma_host, port=s.chroma_port)
        self._client.heartbeat()
        logger.info("ChromaDB connected", extra={"meta": f"{s.chroma_host}:{s.chroma_port}"})

    async def disconnect(self) -> None:
        self._client = None
        logger.info("ChromaDB client released")

    def _get_collection(self):
        if self._client is None:
            raise RuntimeError("ChromaDB not connected")
        return self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    async def store_decision_embedding(
        self,
        decision_id: str,
        text: str,
        metadata: dict | None = None,
    ) -> None:
        await self.store_memory(decision_id, text, "decision", metadata)

    async def store_memory(
        self,
        memory_id: str,
        text: str,
        kind: str,
        metadata: dict | None = None,
    ) -> None:
        collection = self._get_collection()
        meta = metadata or {}
        meta["kind"] = kind
        meta = {k: str(v) for k, v in meta.items()}
        collection.upsert(ids=[memory_id], documents=[text], metadatas=[meta])
        logger.info(f"Embedding stored for {memory_id[:12]}...")

    async def search_similar(self, query_text: str, n_results: int = 5) -> list[dict]:
        collection = self._get_collection()
        results = collection.query(query_texts=[query_text], n_results=n_results)
        matches = []
        if results and results.get("ids"):
            for i, doc_id in enumerate(results["ids"][0]):
                matches.append({
                    "id": doc_id,
                    "document": results["documents"][0][i] if results.get("documents") else "",
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                })
        return matches

    async def get_collection_count(self) -> int:
        try:
            collection = self._get_collection()
            return collection.count()
        except Exception:
            return 0
