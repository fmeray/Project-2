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


# These elements usually contain site chrome rather than source content.
_BOILERPLATE_SELECTORS = [
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "dialog",
    "[role='banner']",
    "[role='navigation']",
    "[role='complementary']",
    "[aria-label*='cookie' i]",
    "[aria-label*='menu' i]",
    "[class*='cookie' i]",
    "[id*='cookie' i]",
    "[class*='consent' i]",
    "[id*='consent' i]",
    "[class*='newsletter' i]",
    "[class*='popup' i]",
    "[class*='modal' i]",
    "[class*='breadcrumb' i]",
    "[class*='social' i]",
    "[class*='share' i]",
    "[class*='menu' i]",
]


def clean_text(text: str) -> str:
    """Normalize extracted text and remove common website boilerplate."""

    lines = []
    previous = None
    for line in text.splitlines():
        line = " ".join(line.split()).strip()
        if not line or line == previous:
            continue
        # These are common leftovers from client-side website rendering.
        lowered = line.lower()
        if lowered.startswith(("javascript:", "data:text/", "webpack", "__next")):
            continue
        lines.append(line)
        previous = line
    return "\n".join(lines).strip()


def _extract_readable_text(html: str, title: str = "") -> str:
    """Extract the most useful readable section from an HTML page."""

    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise RuntimeError(
            "Install the URL-ingestion dependencies with: "
            "pip install -r requirements.txt"
        ) from exc

    soup = BeautifulSoup(html, "html.parser")
    for element in soup.select(", ".join(_BOILERPLATE_SELECTORS)):
        element.decompose()
    for element in soup(["script", "style", "noscript", "template", "svg", "canvas"]):
        element.decompose()

    candidates = soup.find_all(["article", "main"])
    if not candidates:
        candidates = soup.find_all("body") or [soup]
    readable = max(
        (clean_text(element.get_text("\n", strip=True)) for element in candidates),
        key=len,
    )
    if title and not readable.startswith(title):
        readable = f"{title}\n\n{readable}"
    return clean_text(readable)


@dataclass(frozen=True)
class Document:
    """Clean text extracted from one source page."""

    path: str | Path
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
    title = soup.title.get_text(" ", strip=True) if soup.title else url
    text = _extract_readable_text(response.text, title=title)
    if not text:
        raise ValueError(f"No readable text found at {url}")

    return Document(
        path=url,
        text=text,
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


def load_markdown(
    directory: Path, source_type: str = "secondary"
) -> list[Document]:
    """Load Markdown files as documents for the same RAG pipeline."""
    if not directory.exists():
        return []

    documents: list[Document] = []
    for path in sorted(directory.rglob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        if text:
            documents.append(
                Document(
                    path=path,
                    text=text,
                    source_type=source_type,
                    metadata={
                        "source_file": str(path),
                        "title": path.stem,
                        "source_type": source_type,
                    },
                )
            )
    return documents


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
        text = clean_text("\n".join(lines[2:]))
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
    refresh: bool = False,
) -> list[Document]:
    """Load cached pages, optionally refreshing them from their URLs.

    Set ``refresh=True`` after changing the HTML cleaner so existing cache
    files are regenerated from the original pages rather than cleaned after
    their HTML structure has already been lost.
    """
    cached = {} if refresh else load_saved_documents(output_dir)
    documents: list[Document] = []

    for url in WEBSITE_URLS:
        if url in cached:
            documents.append(cached[url])
        else:
            document = load_url(url)
            documents.append(document)

    # Rewrite cached files as well as newly fetched files. This migrates older
    # cache entries through the cleaner without requiring a network request.
    if documents:
        save_documents(documents, output_dir)

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
