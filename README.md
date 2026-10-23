# FREITAG AI Content Creator

This project generates multi-channel FREITAG marketing content grounded in
primary company documents and secondary industry research.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="your-key"
export OPENAI_MODEL="your-model"
```

Alternatively, place `OPENAI_API_KEY` and `OPENAI_MODEL` in `.env` and load
them through your preferred environment tooling.

## Run

```bash
PYTHONPATH=src python src/main.py "Create a product-focused post" --channel LinkedIn
```

The command generates a draft and pauses for human review. Press Enter to
approve and save it in `outputs/`; enter feedback to force a rewrite using that
feedback, then review the new draft. Nothing is saved until approval.

Use `--no-llm` to test retrieval and prompt rendering without an API call.

Launch the Gradio interface with:

```bash
PYTHONPATH=src python src/app.py
```

The interface separates prompt building, draft generation, reviewer feedback,
approval, and optional delivery. A draft is not delivered until it has been
explicitly approved.

To deliver an approved draft, add the relevant platform settings to `.env` and
run with `--deliver`. Delivery is disabled unless
`CONTENT_DELIVERY_ENABLED=true`. Email and newsletter delivery ask for the
recipient email after approval; LinkedIn and Instagram use the selected
channel's configured credentials.

Review generated content before publication. See `project_structure.md`,
`agents.md`, and `rag_decision.md` for project guidance and decisions.
