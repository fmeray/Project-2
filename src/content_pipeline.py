"""Orchestrate draft generation, human review, revision, and approval."""

from datetime import datetime
from pathlib import Path
import re
from typing import Callable

from llm_integration import generate_text
from prompt_templates import build_prompt, load_template


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = BASE_DIR / "outputs"


def _output_filename(content_type: str) -> str:
    """Create a safe, timestamped filename for an approved draft."""

    channel = re.sub(r"[^a-z0-9]+", "-", content_type.lower()).strip("-")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{channel or 'draft'}-{timestamp}.txt"


def save_approved_draft(
    draft: str,
    content_type: str,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> Path:
    """Save a human-approved draft and return its path."""

    if not draft.strip():
        raise ValueError("Cannot save an empty draft")
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / _output_filename(content_type)
    path.write_text(draft.strip() + "\n", encoding="utf-8")
    return path


def review_and_revise(
    prompt: dict,
    draft: str,
    *,
    request: str,
    content_type: str,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    generate: Callable[[str, str], str] = generate_text,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[..., None] = print,
) -> Path:
    """Keep revising until the reviewer presses Enter, then save the draft.

    Any non-empty feedback is inserted verbatim into the next user prompt and
    explicitly marked as mandatory revision criteria.
    """

    revision_template = load_template("revision")
    revision_number = 0

    while True:
        print_fn(f"\nDRAFT (revision {revision_number}):\n")
        print_fn(draft)
        print_fn(
            "\nReview the draft. Press Enter to approve, or enter feedback "
            "for a mandatory rewrite."
        )
        try:
            feedback = input_fn("Feedback: ").strip()
        except (EOFError, KeyboardInterrupt) as exc:
            raise RuntimeError("Review cancelled; the draft was not saved.") from exc

        if not feedback:
            path = save_approved_draft(draft, content_type, output_dir)
            print_fn(f"Approved draft saved to: {path}")
            return path

        revision_number += 1
        revision_prompt = revision_template.format(
            request=request,
            draft=draft,
            feedback=feedback,
        )
        print_fn(f"\nApplying reviewer feedback (revision {revision_number})...")
        draft = generate(prompt["system"], revision_prompt)


def generate_and_review(
    request: str,
    content_type: str,
    *,
    limit: int = 4,
    prompt: dict | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    generate: Callable[[str, str], str] = generate_text,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[..., None] = print,
) -> Path:
    """Build a prompt, generate a draft, review it, and save approval."""

    prompt = prompt or build_prompt(
        content_type=content_type,
        request=request,
        limit=limit,
    )
    draft = generate(prompt["system"], prompt["user"])
    return review_and_revise(
        prompt,
        draft,
        request=request,
        content_type=content_type,
        output_dir=output_dir,
        generate=generate,
        input_fn=input_fn,
        print_fn=print_fn,
    )
