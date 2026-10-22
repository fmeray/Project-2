"""Content-generation orchestration."""

from pathlib import Path

from knowledge_base import load_knowledge_base, select_documents
from llm_integration import generate_text
from prompt_templates import render_template


def build_context(documents) -> str:
    return "\n\n".join(
        f"Source: {document.path} ({document.source_type})\n{document.text}"
        for document in documents
    )


def generate_content(question: str, channel: str, root: Path, template_name: str) -> str:
    documents = load_knowledge_base(root / "knowledge_base")
    selected = select_documents(documents, question)
    context = build_context(selected)
    prompt = render_template(
        template_name,
        {"question": question, "channel": channel, "context": context},
        root / "templates",
    )
    return generate_text(prompt)
