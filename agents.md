# Agent instructions — FREITAG AI Content Studio

## Purpose

Maintain a source-grounded content workflow for Instagram, LinkedIn, email, and
newsletters. The workflow retrieves relevant evidence, builds a channel-specific
prompt, creates a draft, and pauses for human review. Feedback is mandatory input
to every rewrite. Nothing is approved, saved, or delivered automatically.

Consult `project_structure.md` for ownership and `rag_decision.md` for retrieval
behavior before changing architecture.

## Stack and commands

- Python; dependencies are declared in `requirements.txt`.
- Gradio is the UI, while `src/main.py` is the CLI orchestrator.
- BeautifulSoup cleans fetched HTML; cached `.txt` files avoid unnecessary fetches.
- OpenAI is accessed through `src/llm_integration.py`.
- LangChain text splitting and Pinecone are optional retrieval/indexing capabilities.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Gradio UI
PYTHONPATH=src python src/app.py

# CLI workflow
PYTHONPATH=src python src/main.py "Create a product-focused post" --channel LinkedIn
```

Required LLM configuration is `OPENAI_API_KEY` and `OPENAI_MODEL`, in the shell or
local `.env`. Delivery additionally uses `CONTENT_DELIVERY_ENABLED=true` and the
settings documented in `README.md` for SMTP, LinkedIn, or Instagram. Never commit
credentials or place them in prompts, logs, or source files.

## Repository map

- `src/app.py` — Gradio layout and callbacks; do not expose internal prompts in the UI.
- `src/main.py` — terminal entry point and end-to-end orchestration.
- `src/content_pipeline.py` — retrieval, prompt generation, review, revision, and approval.
- `src/content_delivery.py` — explicit, environment-gated platform/email delivery.
- `src/document_processor.py` — HTML cleaning, cache reads, and optional refresh.
- `src/knowledge_base.py` — primary/secondary loading and retrieval helpers.
- `src/prompt_templates.py` — channel selection and prompt rendering.
- `src/llm_integration.py` — OpenAI client setup and clear failures.
- `templates/` — shared, channel, answer, comparison, and revision instructions.
- `knowledge_base/primary/` — authoritative cached FREITAG sources.
- `knowledge_base/secondary/` — supporting research.
- `outputs/` — approved drafts only; ignored by Git.

## Development conventions

1. Keep primary and secondary metadata separate. Primary sources are authoritative;
   secondary material may add context but cannot override them.
2. Let retrieval choose the context. Do not add a user-facing “number of files”
   control or hard-code a fixed source list in the UI.
3. Put channel behavior in `templates/*.md`, not in long Python prompt strings.
4. Preserve source paths/URLs in context and source summaries.
5. Treat reviewer feedback as mandatory. A rewrite must include the feedback in the
   revision prompt and address every requested change.
6. Write to `outputs/` only after explicit approval. Ask for an email recipient at
   delivery time for email/newsletter channels.
7. Keep delivery opt-in and disabled by default. Use mocks for tests; do not send
   real posts or email during routine verification.

## Definition of done

- The change is in the correct module and the documented commands still work.
- Prompt rendering, source metadata, and the review loop are verified with focused tests or mocked calls.
- Errors for missing model/key/network/configuration are actionable and do not reveal secrets.
- Documentation and requirements match the implementation.
- No unapproved draft is saved and no external delivery occurs without explicit action.

## Never do

- Never commit `.env`, API keys, SMTP passwords, access tokens, or recipient data.
- Never invent FREITAG product, brand, sustainability, price, or availability claims.
- Never let secondary research silently contradict primary evidence.
- Never bypass human approval, auto-publish, or auto-email.
- Never replace a mocked verification with a paid live call without explicit authorization.
- Never use destructive Git or filesystem commands to “clean up” the project.

## Change workflow

Before editing, identify the affected source tier, template, module, and documentation.
After editing, run a focused syntax/test check, inspect the diff, and report changed
files, verification, assumptions, and any remaining environment configuration.
