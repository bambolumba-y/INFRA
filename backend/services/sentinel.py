"""Sentinel system — de-duplication via ChromaDB embeddings and AI scoring."""

from __future__ import annotations

import json
import logging
import uuid

import chromadb

from backend.core.config import settings
from backend.llm.provider_factory import ProviderFactory

logger = logging.getLogger(__name__)

SCORE_SYSTEM_PROMPT = (
    "You are a news credibility analyst. Given a piece of news content, "
    "rate its factual reliability on a scale of 1 to 10 where 1 means "
    "pure marketing hype and 10 means verified factual reporting. "
    "Respond with ONLY a JSON object: {\"score\": <int>, \"reason\": \"<short explanation>\"}."
)

SIMILARITY_THRESHOLD = 0.9


class SentinelService:
    """De-duplicate content via vector similarity and score news credibility."""

    def __init__(self, collection_name: str = "content_vectors") -> None:
        self._chroma_client = chromadb.Client(
            chromadb.Settings(
                persist_directory=settings.chroma_persist_dir,
                anonymized_telemetry=False,
            )
        )
        self._collection = self._chroma_client.get_or_create_collection(
            name=collection_name,
        )
        self._llm = ProviderFactory()

    # ------------------------------------------------------------------
    # De-duplication
    # ------------------------------------------------------------------

    def is_duplicate(self, text: str) -> tuple[bool, str | None]:
        """Check whether *text* is a near-duplicate of existing content.

        Returns ``(is_dup, existing_id)`` where *existing_id* is the matched
        document id when *is_dup* is ``True``.
        """
        results = self._collection.query(query_texts=[text], n_results=1)

        if (
            results
            and results["distances"]
            and results["distances"][0]
        ):
            distance = results["distances"][0][0]
            # ChromaDB returns L2 distance by default; lower = more similar.
            # Convert to a rough cosine similarity approximation.
            similarity = max(0.0, 1.0 - distance / 2.0)
            if similarity >= SIMILARITY_THRESHOLD:
                matched_id = results["ids"][0][0] if results["ids"] else None
                logger.info(
                    "Duplicate detected (similarity=%.3f): %s",
                    similarity,
                    matched_id,
                )
                return True, matched_id

        return False, None

    def add_document(self, text: str, metadata: dict | None = None) -> str:
        """Store a document embedding in ChromaDB and return its id."""
        doc_id = str(uuid.uuid4())
        add_kwargs: dict = {"documents": [text], "ids": [doc_id]}
        if metadata:
            add_kwargs["metadatas"] = [metadata]
        self._collection.add(**add_kwargs)
        return doc_id

    # ------------------------------------------------------------------
    # AI credibility scoring
    # ------------------------------------------------------------------

    async def score_content(self, text: str) -> dict:
        """Use the configured LLM to rate news credibility (1-10)."""
        messages = [
            {"role": "system", "content": SCORE_SYSTEM_PROMPT},
            {"role": "user", "content": text[:4000]},
        ]
        response = await self._llm.completion(messages=messages)
        try:
            result = json.loads(response.content)
            return {"score": int(result.get("score", 5)), "reason": result.get("reason", "")}
        except (json.JSONDecodeError, ValueError, TypeError):
            logger.warning("LLM returned non-JSON score response: %s", response.content)
            return {"score": 5, "reason": "Unable to parse LLM response"}

    # ------------------------------------------------------------------
    # Combined pipeline entry-point
    # ------------------------------------------------------------------

    async def process(
        self, text: str, metadata: dict | None = None
    ) -> dict:
        """Run dedup check → AI scoring → store if novel.

        Returns a dict with keys: ``is_duplicate``, ``vector_id``, ``score``,
        ``reason``.
        """
        is_dup, existing_id = self.is_duplicate(text)
        if is_dup:
            return {
                "is_duplicate": True,
                "vector_id": existing_id,
                "score": None,
                "reason": "Duplicate content detected",
            }

        score_result = await self.score_content(text)
        vector_id = self.add_document(text, metadata=metadata)

        return {
            "is_duplicate": False,
            "vector_id": vector_id,
            "score": score_result["score"],
            "reason": score_result["reason"],
        }
