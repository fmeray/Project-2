
"""Send rendered prompts to the configured OpenAI model."""

import os
from pathlib import Path


class LLMConfigurationError(RuntimeError):
    """Raised when the OpenAI client configuration is incomplete."""


class LLMRequestError(RuntimeError):
    """Raised when an OpenAI request fails or returns no text."""


def _load_local_env_fallback() -> None:
    """Read simple KEY=VALUE entries when python-dotenv is unavailable."""

    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


def _load_settings() -> tuple[str, str]:
    """Load and validate the API key and model from the environment or .env."""

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        # Shell/CI environment variables still work without python-dotenv.
        _load_local_env_fallback()

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "").strip()
    if not api_key:
        raise LLMConfigurationError(
            "OPENAI_API_KEY is missing. Add it to .env or the environment."
        )
    if not model:
        raise LLMConfigurationError(
            "OPENAI_MODEL is missing. Add the model name to .env or the environment."
        )
    return api_key, model


def generate_text(system_prompt: str, user_prompt: str | None = None) -> str:
    """Send system and user prompts to OpenAI and return the answer as text.

    The one-argument form is retained for callers that used the original
    messenger; it sends that value as the user prompt without system rules.
    """

    if user_prompt is None:
        user_prompt = system_prompt
        system_prompt = ""
    if not isinstance(system_prompt, str) or not isinstance(user_prompt, str):
        raise ValueError("system_prompt and user_prompt must be strings")
    if not user_prompt.strip():
        raise ValueError("user_prompt must not be empty")

    api_key, model = _load_settings()

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMConfigurationError(
            "The OpenAI package is not installed. Run: pip install -r requirements.txt"
        ) from exc

    messages = []
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(model=model, input=messages)
    except Exception as exc:
        raise LLMRequestError(
            "OpenAI request failed. Check the API key, model name, and network connection."
        ) from exc

    answer = getattr(response, "output_text", "")
    if not isinstance(answer, str) or not answer.strip():
        raise LLMRequestError("OpenAI returned an empty text response.")
    return answer.strip()


def send_prompt(system_prompt: str, user_prompt: str) -> str:
    """Explicit alias for the system/user messenger interface."""

    return generate_text(system_prompt, user_prompt)
