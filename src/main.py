"""Test the website loader and LangChain chunking step."""

import argparse
from pathlib import Path

from knowledge_base import chunk_documents, load_knowledge_base


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch configured webpages and inspect their RAG chunks"
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
        help="Print the full text of every chunk",
    )
    parser.add_argument(
        "--save-dir",
        type=Path,
        help="Save scraped pages as .txt files in this directory",
    )
    parser.add_argument(
        "--save-only",
        action="store_true",
        help="Save webpages and stop before chunking",
    )
    args = parser.parse_args()

    output_dir = args.save_dir or Path("knowledge_base/primary")
    documents = load_knowledge_base(website_cache_dir=output_dir)
    print(f"Loaded documents: {len(documents)} from {output_dir}")
    if args.save_only:
        return
    chunks = chunk_documents(
        documents,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
    )

    print(f"Fetched documents: {len(documents)}")
    print(f"Created chunks: {len(chunks)}")

    for index, chunk in enumerate(chunks, start=1):
        print("\n" + "=" * 80)
        print(f"Chunk {index}/{len(chunks)}")
        print(f"Source: {chunk.metadata.get('title', 'Unknown title')}")
        print(f"URL: {chunk.metadata.get('source_url', 'Unknown URL')}")
        print(f"Characters: {len(chunk.text)}")
        if args.show_text:
            print(f"\n{chunk.text}")


if __name__ == "__main__":
    main()
