"""Load website documents and prepare them for retrieval-augmented generation."""

import math
import os
from dataclasses import dataclass
from pathlib import Path

from src.document_processor import Document, load_markdown, load_website_documents

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # Shell environment variables still work if python-dotenv is unavailable.
    pass


@dataclass(frozen=True)
class Chunk:
    """A retrievable section of a source document."""

    text: str
    metadata: dict[str, str]


@dataclass(frozen=True)
class EmbeddedChunk:
    """A text chunk together with its vector embedding."""

    chunk: Chunk
    embedding: list[float]


def load_knowledge_base(
    website_cache_dir="knowledge_base/primary",
    secondary_dir="knowledge_base/secondary",
) -> list[Document]:
    """Load website documents and secondary Markdown documents together."""
    website_documents = load_website_documents(Path(website_cache_dir))
    markdown_documents = load_markdown(
        Path(secondary_dir), source_type="secondary"
    )
    return website_documents + markdown_documents


def chunk_documents(
    documents: list[Document], chunk_size: int = 500, overlap: int = 50
) -> list[Chunk]:
    """Split documents with LangChain's recursive character splitter."""
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError as exc:
        raise RuntimeError(
            "Install the LangChain splitter with: "
            "pip install langchain-text-splitters"
        ) from exc

    chunks: list[Chunk] = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    for document in documents:
        for index, text in enumerate(splitter.split_text(document.text)):
            metadata = dict(document.metadata)
            metadata.update(
                {
                    "source_url": document.metadata.get(
                        "source_url", str(document.path)
                    ),
                    "chunk_index": str(index),
                }
            )
            chunks.append(Chunk(text=text, metadata=metadata))
    return chunks


def _create_embeddings(texts: list[str], model: str | None = None) -> list[list[float]]:
    """Create OpenAI embeddings for a list of texts."""
    if not texts:
        return []
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install dependencies with: pip install -r requirements.txt") from exc

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(
        model=model or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        input=texts,
    )
    return [item.embedding for item in response.data]


def embed_chunks(
    chunks: list[Chunk], model: str | None = None
) -> list[EmbeddedChunk]:
    """Embed all chunks so they can be searched semantically."""
    vectors = _create_embeddings([chunk.text for chunk in chunks], model=model)
    return [EmbeddedChunk(chunk=chunk, embedding=vector) for chunk, vector in zip(chunks, vectors)]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def retrieve(
    query: str,
    embedded_chunks: list[EmbeddedChunk],
    top_k: int = 5,
    model: str | None = None,
) -> list[Chunk]:
    """Return the chunks most semantically similar to a query."""
    if top_k <= 0:
        return []
    query_embedding = _create_embeddings([query], model=model)[0]
    ranked = sorted(
        embedded_chunks,
        key=lambda item: _cosine_similarity(query_embedding, item.embedding),
        reverse=True,
    )
    return [item.chunk for item in ranked[:top_k]]


def prepare_rag_index(documents: list[Document] | None = None) -> list[EmbeddedChunk]:
    """Fetch documents, chunk them, and create their embedding index."""
    source_documents = documents if documents is not None else load_knowledge_base()
    return embed_chunks(chunk_documents(source_documents))


def select_documents(
    documents: list[Document], query: str, limit: int = 4
) -> list[Document]:
    """Return the pages containing the most terms from a user query."""
    terms = {term.lower() for term in query.split() if len(term) > 2}

    def score(document: Document) -> int:
        text = document.text.lower()
        return sum(term in text for term in terms)

    return sorted(documents, key=score, reverse=True)[:limit]


def search_knowledge_base(query: str, limit: int = 4) -> list[Document]:
    """Fetch the website knowledge base and return relevant documents."""
    documents = load_knowledge_base()
    return select_documents(documents, query, limit=limit)


def build_context(documents: list[Document] | list[Chunk]) -> str:
    """Format retrieved documents, including source metadata, for an LLM."""
    return "\n\n".join(
        (
            f"Source: {document.metadata.get('title', document.metadata.get('source_url', 'web'))}\n"
            f"URL/file: {document.metadata.get('source_url', document.metadata.get('source_file', 'unknown'))}\n"
            f"{document.text}"
        )
        for document in documents
    )
