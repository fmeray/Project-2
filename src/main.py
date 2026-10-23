"""Run the FREITAG retrieval, prompt-rendering, and LLM smoke test."""

import argparse
import sys
from pathlib import Path

from knowledge_base import chunk_documents, load_knowledge_base
from content_delivery import deliver_content
from content_pipeline import generate_and_review
from prompt_templates import CONTENT_TYPES, build_prompt


DEFAULT_REQUEST = "Create a post about FREITAG's circular materials."


def _print_chunk_report(documents, chunk_size, overlap, show_text):
    """Optionally inspect the chunks used by the retrieval pipeline."""

    chunks = chunk_documents(documents, chunk_size=chunk_size, overlap=overlap)
    print(f"Created chunks: {len(chunks)}")
    for index, chunk in enumerate(chunks, start=1):
        print("\n" + "=" * 80)
        print(f"Chunk {index}/{len(chunks)}")
        print(f"Source: {chunk.metadata.get('title', 'Unknown title')}")
        print(f"URL/file: {chunk.metadata.get('source_url', 'Unknown source')}")
        print(f"Characters: {len(chunk.text)}")
        if show_text:
            print(f"\n{chunk.text}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the FREITAG RAG and OpenAI integration smoke test"
    )
    parser.add_argument(
        "request",
        nargs="?",
        default=DEFAULT_REQUEST,
        help=f"Content request (default: {DEFAULT_REQUEST!r})",
    )
    parser.add_argument(
        "--channel",
        default="instagram",
        choices=CONTENT_TYPES,
        help="Prompt template/content type (default: instagram)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=4,
        help="Maximum number of retrieved documents (default: 4)",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refetch website pages and regenerate the cleaned cache",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Stop after prompt rendering without making an OpenAI request",
    )
    parser.add_argument(
        "--inspect-chunks",
        action="store_true",
        help="Also run and print the LangChain chunking diagnostic",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Maximum characters per chunk (default: 500)",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=50,
        help="Overlapping characters between chunks (default: 50)",
    )
    parser.add_argument(
        "--show-text",
        action="store_true",
        help="Print the full text of every diagnostic chunk",
    )
    parser.add_argument(
        "--save-dir",
        type=Path,
        help="Website cache directory (default: knowledge_base/primary)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory for human-approved drafts (default: outputs)",
    )
    parser.add_argument(
        "--deliver",
        action="store_true",
        help="After approval, publish/send through the selected channel",
    )
    args = parser.parse_args()

    if args.deliver and args.no_llm:
        parser.error("--deliver cannot be used with --no-llm")
    if args.limit <= 0:
        parser.error("--limit must be greater than zero")
    if args.chunk_size <= 0 or args.overlap < 0:
        parser.error("--chunk-size must be positive and --overlap cannot be negative")

    output_dir = args.save_dir or Path("knowledge_base/primary")

    try:
        print("STEP 1/4: Loading knowledge base")
        documents = load_knowledge_base(
            website_cache_dir=output_dir,
            refresh=args.refresh,
        )
        print(f"Loaded documents: {len(documents)}")

        if args.inspect_chunks:
            _print_chunk_report(
                documents,
                chunk_size=args.chunk_size,
                overlap=args.overlap,
                show_text=args.show_text,
            )

        print("\nSTEP 2/4: Building prompts")
        prompt = build_prompt(
            content_type=args.channel,
            request=args.request,
            limit=args.limit,
        )
        print(f"Template: {args.channel}")
        print(f"Retrieved documents: {len(prompt['documents'])}")
        print(f"System prompt characters: {len(prompt['system'])}")
        print(f"User prompt characters: {len(prompt['user'])}")

        print("\nSOURCES:")
        for document in prompt["documents"]:
            print("-", document.metadata.get("title", document.path))

        print("\nSYSTEM PROMPT PREVIEW:")
        print(prompt["system"][:500])
        print("\nUSER PROMPT PREVIEW:")
        print(prompt["user"][:1000])

        if args.no_llm:
            print("\nLLM call skipped (--no-llm). Prompt pipeline completed.")
            return

        print("\nSTEP 3/4: Sending system + user prompts to OpenAI")
        print("STEP 4/4: Starting human review")
        approved_path = generate_and_review(
            request=args.request,
            content_type=args.channel,
            limit=args.limit,
            prompt=prompt,
            output_dir=args.output_dir,
        )
        print(f"\nWorkflow completed. Approved draft: {approved_path}")

        if args.deliver:
            approved_content = approved_path.read_text(encoding="utf-8")
            recipient_email = None
            if args.channel in {"email", "newsletter"}:
                recipient_email = input("Recipient email: ").strip()
            delivery = deliver_content(
                args.channel,
                approved_content,
                recipient_email=recipient_email,
            )
            print(
                f"Delivered via {delivery.channel} to {delivery.destination} "
                f"(ID: {delivery.external_id})."
            )
    except Exception as exc:
        print(f"\nSmoke test failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
