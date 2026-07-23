from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import chromadb
from chromadb.config import Settings

from app.rag.chunking import chunk_document
from app.rag.embeddings import Embedder


@dataclass(frozen=True)
class SearchMatch:
    chunk_id: str
    text: str
    source_id: str
    source: str
    title: str
    chunk_index: int
    score: float


class KnowledgeBaseStore:
    def __init__(
        self,
        path: str | Path,
        embedder: Embedder,
        collection_name: str = "astratickets_knowledge",
    ) -> None:
        self.client = chromadb.PersistentClient(
            path=str(path),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.embedder = embedder

    def ingest(
        self,
        *,
        text: str,
        title: str,
        source: str,
        source_id: str | None = None,
    ) -> tuple[str, int]:
        chunks = chunk_document(text)
        if not chunks:
            raise ValueError("Document text cannot be empty")

        resolved_source_id = source_id or sha256(source.encode("utf-8")).hexdigest()[:20]
        self.collection.delete(where={"source_id": resolved_source_id})
        ids = [f"{resolved_source_id}:{index}" for index in range(len(chunks))]
        metadatas = [
            {
                "source_id": resolved_source_id,
                "source": source,
                "title": title,
                "chunk_index": index,
            }
            for index in range(len(chunks))
        ]
        self.collection.upsert(
            ids=ids,
            documents=chunks,
            metadatas=metadatas,
            embeddings=self.embedder.encode(chunks),
        )
        return resolved_source_id, len(chunks)

    def search(self, query: str, limit: int = 5) -> list[SearchMatch]:
        if not query.strip():
            raise ValueError("Search query cannot be empty")
        if self.collection.count() == 0:
            return []

        result = self.collection.query(
            query_embeddings=self.embedder.encode([query]),
            n_results=min(limit, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        ids = (result.get("ids") or [[]])[0]
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        matches: list[SearchMatch] = []
        for chunk_id, text, metadata, distance in zip(
            ids,
            documents,
            metadatas,
            distances,
            strict=True,
        ):
            if text is None or metadata is None:
                continue
            matches.append(
                SearchMatch(
                    chunk_id=chunk_id,
                    text=text,
                    source_id=str(metadata["source_id"]),
                    source=str(metadata["source"]),
                    title=str(metadata["title"]),
                    chunk_index=int(metadata["chunk_index"]),
                    score=max(0.0, min(1.0, 1.0 - float(distance))),
                )
            )
        return matches
