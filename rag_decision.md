# RAG decision

## Decision

Keep retrieval-augmented generation (RAG), with a lightweight local retrieval path
as the current default and semantic/vector retrieval as an optional extension.

The application does not send the complete knowledge base to the model. It loads
cleaned sources, selects relevant documents, separates primary from secondary
evidence, and renders only that context into the selected channel template.

## Why RAG fits this project

1. **Grounding.** FREITAG-specific claims should come from the supplied official
   sources rather than general model memory.
2. **Different requests and channels.** Product, brand, materials, comparison, and
   campaign requests need different evidence, while the same corpus supports all
   four delivery formats: Instagram, LinkedIn, email, and newsletter.
3. **Traceability.** Source titles, URLs, paths, and source tiers remain available
   to the reviewer and are shown in the application’s resource summary.
4. **Maintainability.** Sources, retrieval logic, and prompt templates can change
   independently. New sources do not require rewriting every channel prompt.
5. **Cost and context control.** Relevant context is smaller than the full corpus,
   reducing unnecessary prompt tokens and making the workflow easier to scale.

## Current implementation

### Ingestion and cleaning

`src/document_processor.py` fetches configured website pages when needed, removes
scripts, styles, navigation, cookie banners, forms, and other page boilerplate,
normalizes whitespace, and stores cleaned text in `knowledge_base/primary/`.
Existing `.txt` cache files are reused. A caller can pass `refresh=True` to fetch
and clean the URLs again.

Secondary Markdown files are loaded from `knowledge_base/secondary/`. Every document
keeps metadata such as source type, title, URL, and file path.

### Retrieval choice

The normal application path uses `search_knowledge_base()` and `select_documents()`
for fast, deterministic term-based document matching. The retrieval limit is an
internal pipeline decision; the Gradio user does not choose how many files to use.
This is the right baseline for the current small corpus and keeps the app usable
without an embedding service.

`chunk_documents()`, `embed_chunks()`, `retrieve()`, and `prepare_rag_index()` are
available for semantic retrieval when the corpus or query complexity justifies it.
`src/Pinecone.py` can provide persistence for that index. These are extensions,
not prerequisites for the current UI or CLI workflow.

### Prompt construction

`src/prompt_templates.py` selects the channel template and renders both prompts:

- `templates/system.md` supplies shared grounding, tone, and safety rules.
- The selected `instagram.md`, `linkedin.md`, `email.md`, or `newsletter.md` file
  supplies channel-specific output rules.
- `{request}` contains the user’s content request.
- `{primary}` contains authoritative retrieved evidence.
- `{secondary}` contains supporting research, when relevant.

`answer_with_context.md` and `compare_sources.md` support non-publishing requests.
`revision.md` receives the current draft and the reviewer’s feedback; the feedback
is explicitly mandatory for the next version.

## Evidence and review safeguards

- Primary FREITAG material is authoritative.
- Secondary research can provide context but cannot silently override primary material.
- Insufficient evidence should remain visible rather than being filled with invented claims.
- The draft is displayed with its retrieved resources for human review.
- Empty approval saves the draft to `outputs/`; feedback triggers another generation cycle.
- Delivery is a separate explicit action and is disabled unless the environment enables it.
- Email/newsletter delivery asks for the recipient after approval, so email is optional during drafting.

## Alternatives considered

### Full-context injection

This would be simple for a tiny, stable corpus, but it sends unrelated text for every
request, increases prompt size, and makes source prioritization less explicit. It is
not the current choice.

### Semantic retrieval as the only default

Embeddings can improve matching for paraphrased queries, but they add configuration,
latency, and API cost. The current lexical baseline is more reproducible for this
small corpus. Semantic retrieval remains available when evaluation shows that it is
needed.

### Fine-tuning

Fine-tuning is not appropriate for frequently changing source facts or a small
project corpus. It would also make provenance and rapid source updates harder.

## Revisit criteria

Promote semantic or Pinecone retrieval to the default if the corpus grows materially,
term matching misses relevant paraphrases in evaluation, or repeated users need
cross-document semantic search. Re-evaluate source cleaning if cached pages gain
substantial boilerplate or source freshness becomes a business requirement.
