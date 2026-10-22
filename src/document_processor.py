"""Fetch website pages and convert them into documents for RAG."""

from dataclasses import dataclass, field
import re
from pathlib import Path
from urllib.parse import urlparse


# Paste the website pages you want to use here.
# These are examples; replace them with the real URLs.
WEBSITE_URLS = [
     "https://freitag.ch/en_DE/mission/impact-statements",
     "https://freitag.ch/en_DE/mission/about-freitag",
     "https://freitag.ch/en_DE/mission/about-freitag/history",
     "https://freitag.ch/en_DE/mission/about-freitag/material-cycle",
     "https://freitag.ch/en_DE/mission/product-stories/small-shoulder-bag",
     "https://freitag.ch/en_DE/mission/product-stories/reference-line",

]


@dataclass(frozen=True)
class Document:
    """Clean text extracted from one source page."""

    path: str
    text: str
    source_type: str = "web"
    metadata: dict[str, str] = field(default_factory=dict)


def load_url(url: str, timeout: int = 20) -> Document:
    """Fetch one webpage and return its readable text.

    The webpage is fetched and processed in memory. It is not saved as a PDF
    or as an HTML file.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise RuntimeError(
            "Install the URL-ingestion dependencies with: "
            "pip install -r requirements.txt"
        ) from exc

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid URL; use http:// or https://: {url}")

    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "FREITAG-RAG-document-loader/1.0"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for element in soup(["script", "style", "noscript", "template", "svg"]):
        element.decompose()

    # Some sites put only a short introduction in <main> while the complete
    # page is in <body>. Choose the largest readable container instead of
    # assuming that the first <main> or <article> contains everything.
    candidates = [element for element in soup.find_all(["article", "main", "body"])]
    if not candidates:
        candidates = [soup]
    text = max(
        (" ".join(element.get_text(" ", strip=True).split()) for element in candidates),
        key=len,
    )
    if not text:
        raise ValueError(f"No readable text found at {url}")

    title = soup.title.get_text(" ", strip=True) if soup.title else url
    return Document(
        path=url,
        text=f"{title}\n\n{text}",
        metadata={
            "source_url": url,
            "title": title,
            "source_type": "web",
        },
    )


def load_urls(urls: list[str]) -> list[Document]:
    """Fetch every URL in *urls* as a separate RAG document."""
    if not urls:
        raise ValueError("Add at least one URL to WEBSITE_URLS or pass a URL list")
    return [load_url(url) for url in urls]


def load_saved_documents(output_dir: Path) -> dict[str, Document]:
    """Read previously fetched text files, indexed by their source URL."""
    if not output_dir.exists():
        return {}

    cached: dict[str, Document] = {}
    for path in sorted(output_dir.glob("*.txt")):
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines or not lines[0].startswith("Source URL: "):
            continue

        url = lines[0].removeprefix("Source URL: ").strip()
        text = "\n".join(lines[2:]).strip()
        title = text.splitlines()[0] if text else path.stem
        cached[url] = Document(
            path=url,
            text=text,
            metadata={
                "source_url": url,
                "title": title,
                "source_type": "web",
                "cached_file": str(path),
            },
        )
    return cached


def load_website_documents(
    output_dir: Path = Path("knowledge_base/primary"),
) -> list[Document]:
    """Load cached pages and fetch only URLs not already saved locally."""
    cached = load_saved_documents(output_dir)
    documents: list[Document] = []
    new_documents: list[Document] = []

    for url in WEBSITE_URLS:
        if url in cached:
            documents.append(cached[url])
        else:
            document = load_url(url)
            documents.append(document)
            new_documents.append(document)

    if new_documents:
        save_documents(new_documents, output_dir)

    return documents


def save_documents(
    documents: list[Document], output_dir: Path
) -> list[Path]:
    """Save scraped documents as text files and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: list[Path] = []

    for index, document in enumerate(documents, start=1):
        title = document.metadata.get("title", "webpage")
        filename = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower()
        filename = filename or f"webpage-{index}"
        path = output_dir / f"{filename}.txt"

        # Include provenance in the text file so the source remains traceable.
        source_url = document.metadata.get("source_url", document.path)
        content = f"Source URL: {source_url}\n\n{document.text}\n"
        path.write_text(content, encoding="utf-8")
        saved_paths.append(path)

    return saved_paths


def fetch_and_save_website_documents(
    output_dir: Path = Path("knowledge_base/primary"),
) -> list[Path]:
    """Fetch configured webpages and save them as text files."""
    return save_documents(load_website_documents(), output_dir)
