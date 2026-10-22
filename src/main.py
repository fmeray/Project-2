"""Command-line entry point for the FREITAG content pipeline."""

import argparse
from pathlib import Path

from content_pipeline import generate_content


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate grounded FREITAG content")
    parser.add_argument("question", help="Content request or question")
    parser.add_argument("--channel", default="LinkedIn", help="Target channel")
    parser.add_argument("--template", default="answer_with_context.md")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    print(generate_content(args.question, args.channel, root, args.template))


if __name__ == "__main__":
    main()
