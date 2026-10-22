"""Store the embedded RAG chunks in Pinecone."""

import hashlib
import os
import time

from knowledge_base import EmbeddedChunk, prepare_rag_index


def _vector_id(item: EmbeddedChunk) -> str:
    """Create a stable ID so rerunning the upload updates the same chunk."""
    source = item.chunk.metadata.get("source_url", "unknown")
    chunk_index = item.chunk.metadata.get("chunk_index", "0")
    raw_id = f"{source}:{chunk_index}:{item.chunk.text}"
    return hashlib.sha256(raw_id.encode("utf-8")).hexdigest()


def _get_index(client, index_name: str, dimension: int):
    """Create a serverless index when it does not already exist."""
    from pinecone import ServerlessSpec

    existing_indexes = client.list_indexes().names()
    if index_name not in existing_indexes:
        client.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=os.getenv("PINECONE_CLOUD", "aws"),
                region=os.getenv("PINECONE_REGION", "us-east-1"),
            ),
        )

        while not client.describe_index(index_name).status["ready"]:
            time.sleep(1)

    return client.Index(index_name)


def upsert_embedded_chunks(
    embedded_chunks: list[EmbeddedChunk],
    index_name: str | None = None,
    namespace: str = "freitag",
    batch_size: int = 100,
) -> int:
    """Upsert embedded chunks and metadata into Pinecone."""
    if not embedded_chunks:
        return 0

    try:
        from pinecone import Pinecone
    except ImportError as exc:
        raise RuntimeError(
            "Install the Pinecone SDK with: pip install -r requirements.txt"
        ) from exc

    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise RuntimeError("PINECONE_API_KEY is not configured")

    name = index_name or os.getenv("PINECONE_INDEX", "freitag-rag")
    client = Pinecone(api_key=api_key)
    index = _get_index(client, name, len(embedded_chunks[0].embedding))

    vectors = [
        {
            "id": _vector_id(item),
            "values": item.embedding,
            "metadata": {
                **item.chunk.metadata,
                "text": item.chunk.text,
            },
        }
        for item in embedded_chunks
    ]

    for start in range(0, len(vectors), batch_size):
        index.upsert(
            vectors=vectors[start : start + batch_size],
            namespace=namespace,
        )

    return len(vectors)


def main() -> None:
    """Build the current RAG index and upload it to Pinecone."""
    embedded_chunks = prepare_rag_index()
    count = upsert_embedded_chunks(embedded_chunks)
    print(f"Upserted {count} embedded chunks into Pinecone")


if __name__ == "__main__":
    main()
