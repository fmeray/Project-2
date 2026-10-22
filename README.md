# FREITAG AI Content Creator

This project generates multi-channel FREITAG marketing content grounded in
primary company documents and secondary industry research.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="your-key"
```

Alternatively, place `OPENAI_API_KEY` and optional `OPENAI_MODEL` in `.env` and
load them through your preferred environment tooling.

## Run

```bash
PYTHONPATH=src python src/main.py "Create a product-focused post" --channel LinkedIn
```

Review generated content before publication. See `project_structure.md`,
`agents.md`, and `rag_decision.md` for project guidance and decisions.
