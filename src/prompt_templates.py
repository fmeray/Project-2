"""Reusable prompt template loading and rendering."""

from pathlib import Path


def load_template(name: str, directory: Path = Path("templates")) -> str:
    path = directory / name
    return path.read_text(encoding="utf-8")


def render_template(name: str, values: dict[str, str], directory: Path = Path("templates")) -> str:
    template = load_template(name, directory)
    return template.format(**values)
