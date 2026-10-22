"""Markdown loading and lightweight document processing."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Document:
    path: Path
    text: str
    source_type: str


def load_markdown(directory: Path, source_type: str) -> list[Document]:
    """Load all Markdown files below *directory* with source metadata."""
    if not directory.exists():
        return []

    documents: list[Document] = []
    for path in sorted(directory.rglob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        if text:
            documents.append(Document(path=path, text=text, source_type=source_type))
    return documents
