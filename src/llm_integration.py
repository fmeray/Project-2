"""LLM API integration with a safe local fallback."""

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # Environment variables can still be supplied by the shell or CI system.
    pass


def generate_text(prompt: str) -> str:
    """Call the configured OpenAI-compatible client.

    A missing key produces an actionable message instead of silently pretending
    that generated content came from an LLM.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured. Add it to .env before running the pipeline.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install dependencies with: pip install -r requirements.txt") from exc

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        input=prompt,
    )
    return response.output_text
