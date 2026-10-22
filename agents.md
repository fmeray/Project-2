# agents.md — FREITAG AI Content Creator

## Purpose

Maintain a small, reproducible RAG pipeline that creates channel-appropriate
FREITAG marketing drafts for LinkedIn, newsletters, and X. Generated copy must
be grounded in the repository knowledge base, retain source paths for review,
and remain a draft until a human reviewer approves it. `project_structure.md`
and `rag_decision.md` are the project brief and RAG decision; consult them when
the scope or an implementation choice is unclear.

## Stack & run

- Python with dependencies from `requirements.txt` (`openai` and `python-dotenv`).
- Markdown knowledge sources and reusable templates; the LLM is called through
  `src/llm_integration.py`.
- Configure `OPENAI_API_KEY` and optionally `OPENAI_MODEL` in a local `.env`
  file (or the shell environment). Never commit `.env` or real credentials.
- Install and run from the repository root:

  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  PYTHONPATH=src python src/main.py "Create a product-focused post" --channel LinkedIn
  ```

  A live API call requires a configured key. Tests and pipeline checks should
  use a mocked LLM call unless a live integration test is explicitly requested.

## Repository map

- `knowledge_base/primary/` — authoritative FREITAG brand and product material.
- `knowledge_base/secondary/` — supplementary market and competitor research.
- `src/document_processor.py` — load and normalize Markdown with source metadata.
- `src/knowledge_base.py` — keep source types separate and select relevant files.
- `src/prompt_templates.py` and `templates/` — reusable prompt definitions.
- `src/content_pipeline.py` — retrieve context, render prompts, and orchestrate generation.
- `src/llm_integration.py` — environment configuration and LLM error handling.
- `src/main.py` — command-line entry point.
- `README.md`, `project_structure.md`, and `rag_decision.md` — setup, scope, and decisions.

## Conventions

- Preserve `primary` and `secondary` source labels and source paths in retrieved
  context and generated evidence.
- Primary FREITAG documents are authoritative. Secondary research may add
  context but must not override or silently contradict primary material.
- Keep functions small, dependencies explicit, and prompt text reusable in
  `templates/`; do not hard-code long prompts into pipeline logic.
- Put new source documents in the correct knowledge-base tier. Put new prompt
  templates in `templates/` and expose their selection through the existing
  template-loading path.
- Follow the existing import and CLI style. Update the README or project
  documentation when setup, commands, or repository responsibilities change.

## Definition of done

- The requested behavior is implemented in the appropriate module and remains
  compatible with the documented end-to-end command.
- Primary and secondary Markdown sources are ingested, distinguished, and
  retrieved with source paths preserved.
- Prompt changes are reusable templates and include the relevant question,
  channel, and grounded context.
- Pipeline logic is verified with mocked LLM calls; failures are actionable and
  secrets are not logged.
- Documentation and any affected requirements are updated, and the changed
  path has been checked with a focused run or test.
- Generated content is clearly treated as a draft and receives human review
  before publication.

## Never do

- Never commit `.env`, API keys, tokens, or other credentials.
- Never invent or embellish FREITAG product, brand, price, availability,
  sustainability, or impact claims.
- Never let secondary research override an authoritative primary document.
- Never remove source paths from retrieved context or present unsupported text as
  verified fact.
- Never publish generated content automatically or skip required human review.
- Never replace a mocked test with a paid live LLM call just to verify pipeline
  logic.

## How we use agents

Work on one clearly scoped change at a time. Before editing, identify the
affected module, knowledge-base tier, template, and documentation. After
editing, report the files changed, the verification performed, any assumptions,
and any remaining human-review or API configuration requirement.
