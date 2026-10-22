"""Primary and secondary knowledge-base management."""

from pathlib import Path

from document_processor import Document, load_markdown


def load_knowledge_base(root: Path) -> list[Document]:
    """Return primary documents before secondary documents."""
    return load_markdown(root / "primary", "primary") + load_markdown(
        root / "secondary", "secondary"
    )


def select_documents(documents: list[Document], query: str, limit: int = 4) -> list[Document]:
    """Select documents with the most query terms, preferring primary sources."""
    terms = {term.lower() for term in query.split() if len(term) > 2}

    def score(document: Document) -> tuple[int, int]:
        haystack = document.text.lower()
        matches = sum(term in haystack for term in terms)
        primary_bonus = int(document.source_type == "primary")
        return matches, primary_bonus

    ranked = sorted(documents, key=score, reverse=True)
    return ranked[:limit]
