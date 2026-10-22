
from pathlib import Path

from src.knowledge_base import (
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


def load_template(name):
    """Load a Markdown prompt template."""

    if name not in CONTENT_TYPES and name != "system":
        raise ValueError(f"Unknown template: {name}")

    path = TEMPLATE_DIR / f"{name}.md"

    if not path.exists():
        raise FileNotFoundError(f"Missing template: {path}")

    return path.read_text(encoding="utf-8")


def build_prompt(
    content_type,
    question,
    limit=4,
):
    """Build a prompt using relevant FREITAG documents."""

    system_rules = load_template("system")
    template = load_template(content_type)

    documents = search_knowledge_base(
        query=question,
        limit=limit,
    )

    context = build_context(documents)

    user_prompt = template.format(
        question=question,
        channel=content_type,
        context=context,
    )

    return {
        "system": system_rules,
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
