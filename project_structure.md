# Project structure and stakeholder analysis

## Project identity

| Field | Definition |
| --- | --- |
| Project | FREITAG AI Content Studio |
| Goal | Create grounded drafts for Instagram, LinkedIn, email, and newsletters. |
| Quality objective | Keep content channel-appropriate, on-brand, source-supported, and human-reviewed. |
| Delivery objective | Save approved drafts locally and deliver them only when the user explicitly requests it. |
| Security objective | Keep API keys and delivery credentials outside version control. |

The application is an assisted content workflow, not an autonomous publisher. A
human reviews every draft, can request revisions, and approves the final text before
it is saved or delivered.

## Repository structure

```text
Project-2/
├── src/
│   ├── app.py                 # Gradio user interface and workflow callbacks
│   ├── main.py                # CLI orchestrator for the same workflow
│   ├── content_pipeline.py    # Prompt building, generation, review, approval, saving
│   ├── content_delivery.py    # Guarded LinkedIn, Instagram, and email delivery
│   ├── document_processor.py  # URL fetching, HTML cleaning, and text caching
│   ├── knowledge_base.py      # Source loading, metadata, and retrieval helpers
│   ├── prompt_templates.py    # Template selection and prompt rendering
│   ├── llm_integration.py     # OpenAI configuration, request, and error handling
│   ├── Pinecone.py            # Optional persistent vector-index integration
│   └── FREITAG.png            # Gradio background asset
├── templates/                 # Shared, channel, answer, comparison, and revision prompts
├── knowledge_base/
│   ├── primary/               # Cached official FREITAG source text
│   └── secondary/             # Market and competitor context
├── outputs/                   # Approved drafts; ignored by Git
├── requirements.txt
├── README.md
├── agents.md
├── project_structure.md
├── rag_decision.md
└── .env                       # Local configuration; never commit
```

## Component responsibilities

| Location | Responsibility |
| --- | --- |
| `knowledge_base/primary/` | Authoritative FREITAG material fetched from configured web pages and cached as cleaned text. |
| `knowledge_base/secondary/` | Supplementary market and competitor research; never authoritative over primary sources. |
| `src/document_processor.py` | Remove scripts, navigation, cookie UI, boilerplate, and duplicate whitespace; reuse cached `.txt` files unless refresh is requested. |
| `src/knowledge_base.py` | Load both source tiers and preserve source type, title, URL, and file metadata. |
| `src/prompt_templates.py` | Let the selected channel determine the system and user prompt; provide `{request}`, `{primary}`, and `{secondary}`. Retrieval decides the context size. |
| `src/llm_integration.py` | Read OpenAI settings from environment/`.env`, send system plus user prompts, and return text with clear configuration/network errors. |
| `src/content_pipeline.py` | Coordinate retrieval, generation, human feedback, mandatory rewrites, and approval-only saving. |
| `src/content_delivery.py` | Deliver only after approval and explicit user action; disabled unless `CONTENT_DELIVERY_ENABLED=true`. |
| `src/app.py` | Gradio workflow: request → draft → sources → feedback or approval → optional delivery. |
| `src/main.py` | Equivalent terminal workflow and diagnostic entry point. |
| `outputs/` | Approved draft files only; unapproved drafts are not persisted by the pipeline. |

## Stakeholders and safeguards

| Stakeholder | Success criteria | Safeguard |
| --- | --- | --- |
| FREITAG marketing/brand team | Useful, accurate, channel-appropriate content | Primary sources, reusable channel templates, human approval |
| Content reviewer | Can understand the evidence and correct the draft | Source list, visible draft, feedback-driven rewrite loop |
| Channel/email owner | Correct format and intentional delivery | Explicit delivery action and channel-specific connector |
| Project owner/evaluator | Reproducible end-to-end demonstration | README commands, CLI, Gradio app, documented RAG decision |
| Maintainer | Small, testable, replaceable components | Separate ingestion, retrieval, prompting, LLM, review, and delivery modules |
| Security/privacy reviewer | No leaked credentials or accidental publishing | `.env` excluded, delivery disabled by default, no secrets in logs |

## Requirement and verification matrix

| ID | Requirement | Implementation | Verification |
| --- | --- | --- | --- |
| M1 | Clean website text and cache it | `document_processor.py` | Load cached text; use `refresh=True` only when a refetch is intended. |
| M2 | Keep primary and secondary evidence distinct | `knowledge_base.py` | Inspect metadata and rendered prompt sections. |
| M3 | Select a channel-specific prompt | `prompt_templates.py`, `templates/` | Render each channel and verify `{request}`, `{primary}`, and `{secondary}` are filled. |
| M4 | Call the configured LLM | `llm_integration.py` | Run with a mocked client or configured integration test. |
| M5 | Require human review and feedback | `content_pipeline.py`, `app.py`, `main.py` | Feedback produces a rewrite; empty approval saves the draft. |
| M6 | Save only approved drafts | `content_pipeline.py`, `outputs/` | Confirm no file is written before approval. |
| M7 | Support explicit delivery | `content_delivery.py` | Verify delivery is blocked unless enabled and email recipient is entered after approval. |
| M8 | Provide usable interfaces and documentation | `app.py`, `main.py`, `README.md` | Run the documented Gradio or CLI command and complete the workflow. |

## Main risks

- Unsupported or off-brand claims: constrain generation to retrieved evidence and require review.
- Stale or noisy web text: clean and cache documents, and provide an explicit refresh path.
- LLM/API failure: validate configuration and show actionable errors.
- Accidental publication or email: save only after approval and keep delivery disabled by default.
- SMTP or platform configuration errors: report the failing configuration category without exposing secrets.
