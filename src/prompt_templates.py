
from pathlib import Path

from knowledge_base import (
    search_knowledge_base,
    build_context,
)

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"

CONTENT_TYPES = [
    "instagram",
    "linkedin",
    "newsletter",
    "email",
    "answer_with_context",
    "compare_sources",
]


def _normalise_content_type(content_type):
    """Return the template key used on disk for a user-selected channel."""

    return str(content_type).strip().lower().replace("-", "_").replace(" ", "_")


def load_template(name):
    """Load a Markdown prompt template."""

    name = _normalise_content_type(name)
    if name not in CONTENT_TYPES and name not in {"system", "revision"}:
        raise ValueError(f"Unknown template: {name}")

    path = TEMPLATE_DIR / f"{name}.md"

    if not path.exists():
        raise FileNotFoundError(f"Missing template: {path}")

    return path.read_text(encoding="utf-8")


def build_prompt(
    content_type,
    request=None,
    limit=4,
    *,
    question=None,
):
    """Build system and user prompts from the selected content template.

    ``question`` is retained as a backwards-compatible alias for ``request``.
    Retrieved documents are separated into primary and secondary context so
    templates can apply the appropriate level of authority to each source.
    """

    if request is None:
        request = question
    elif question is not None and question != request:
        raise ValueError("Pass either request or question, not both")
    if request is None or not str(request).strip():
        raise ValueError("request must be a non-empty string")

    template_key = _normalise_content_type(content_type)

    system_rules = load_template("system")
    template = load_template(template_key)

    documents = search_knowledge_base(
        query=request,
        limit=limit,
    )

    primary_documents = [
        document
        for document in documents
        if document.source_type != "secondary"
        and document.metadata.get("source_type") != "secondary"
    ]
    secondary_documents = [
        document
        for document in documents
        if document.source_type == "secondary"
        or document.metadata.get("source_type") == "secondary"
    ]

    values = {
        "request": request,
        "primary": build_context(primary_documents),
        "secondary": build_context(secondary_documents),
        # These aliases keep older custom templates working during migration.
        "question": request,
        "channel": template_key,
        "context": build_context(documents),
    }

    system_prompt = system_rules.format(**values)
    user_prompt = template.format(**values)

    return {
        "system": system_prompt,
        "user": user_prompt,
        "documents": documents,
    }


if __name__ == "__main__":

    result = build_prompt(
        content_type="instagram",
        question="Create an Instagram post about FREITAG's circular materials.",
    )

    print("\nFREITAG PROMPT BUILDER")
    print("----------------------")

    print("Documents selected:", len(result["documents"]))

    print("\nSOURCES:")
    for document in result["documents"]:
        print("-", document.metadata.get("title", document.path))

    print("\nSYSTEM PROMPT:")
    print(result["system"])

    print("\nUSER PROMPT PREVIEW:")
    print(result["user"][:1500])

    print("\nPrompt builder completed!")
