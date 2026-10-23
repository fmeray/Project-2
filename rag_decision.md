# RAG decision

## Decision

Use a RAG approach for the FREITAG AI Content
Creator. Do not inject the complete knowledge base into every prompt.

For each request, the application loads the available sources, splits them
into smaller chunks, retrieves the material relevant to the request, and
passes that selected context to the generation step. This keeps the answer
grounded while avoiding a fixed, ever-growing prompt containing the whole
corpus.

## Why RAG fits this project

The choice is based on the shape and intended use of this knowledge base, not
on RAG being mandatory.

1. **Corpus size and structure.** The current repository contains six cached
   official FREITAG web pages in `knowledge_base/primary/` and two secondary
   research files in `knowledge_base/secondary/`. The sources are individually
   substantial and cover different subjects: the brand, history, materials,
   impact statements, and product stories. Injecting all of that material into
   every request would consume context even when only one product or topic is
   relevant. Retrieval selects a smaller, useful subset.

2. **Different requests and channels.** The project must support product,
   brand, and comparison questions and produce drafts for channels such as
   LinkedIn, newsletters, and X. A request about a product should retrieve
   product-story chunks; a request about materials should retrieve the
   relevant materials or impact source. The same corpus can therefore support
   many different questions without maintaining a separate hard-coded prompt
   for each one.

3. **Sources can change or grow.** Official website content and supplementary
   market research are maintained separately from the prompt templates. The
   document loader can use cached pages, add configured URLs, and save source
   text with its URL. Re-running chunking and indexing makes source updates
   available without rewriting the generation prompts.

4. **Context size, cost, and speed.** `knowledge_base.py` uses 500-character
   chunks with 50-character overlap and returns the top five semantic matches
   by default. Only the retrieved chunks need to be placed in the generation
   context. Embedding the corpus and the query adds API cost, but it avoids
   sending unrelated source text on every generation call and gives a better
   path as the corpus grows.

5. **Worth implementing within the project time limit.** This is a small,
   explicit RAG implementation rather than a large platform: documents are
   represented by dataclasses, LangChain supplies the recursive text splitter,
   OpenAI supplies embeddings, and the baseline search ranks vectors with
   cosine similarity. `Pinecone.py` provides an optional persistent vector
   index when that is useful. This delivers retrieval and provenance within the
   two-day project scope without introducing unnecessary orchestration.

## How the decision maps to the code

### 1. Ingest and normalize sources

- `src/document_processor.py` fetches the configured official FREITAG pages,
  removes page elements that are not readable content, and creates `Document`
  objects with titles and source URLs.
- Fetched primary pages are cached as text files under
  `knowledge_base/primary/`. The current loader reads these cached `*.txt`
  files and preserves the original `Source URL`.
- `load_markdown()` reads the secondary `*.md` files under
  `knowledge_base/secondary/` and marks them as secondary sources.
- `load_knowledge_base()` combines the primary website documents and the
  secondary research documents while keeping their metadata available.

### 2. Chunk and represent the corpus

`chunk_documents()` uses LangChain's
`RecursiveCharacterTextSplitter` with a 500-character chunk size and
50-character overlap. Each `Chunk` retains source metadata and receives a
chunk index. `embed_chunks()` creates OpenAI embeddings, using
`text-embedding-3-small` by default or the configured embedding model.

### 3. Retrieve relevant evidence

`retrieve()` embeds the user's query, compares it with the indexed chunks
using cosine similarity, and returns the highest-ranked chunks. The helper
`prepare_rag_index()` performs the load → chunk → embed sequence. The module
also includes `select_documents()` and `search_knowledge_base()` for a
lightweight term-based document search; both are retrieval operations and do
not change the architectural decision.

`src/Pinecone.py` is an optional persistence layer. It uploads the same
embedded chunks to a Pinecone index and keeps the source metadata and text in
the vector metadata. The local in-memory cosine search remains the simple,
reproducible baseline.

### 4. Build grounded context for generation

`build_context()` formats each retrieved document or chunk with its title and
source URL/file path before the context is given to an LLM. The reusable
templates in `templates/` instruct the model to use only the supplied context,
avoid invented facts, identify insufficient evidence, and include sources
used. This makes the output a grounded draft rather than an unsupported
generic response.

## Source priority and review safeguards

- Official FREITAG material in the primary knowledge-base tier is
  authoritative.
- Secondary market and competitor research may add context, but it must not
  override or silently contradict a primary source. The comparison template
  asks the model to distinguish primary support, secondary context, and points
  requiring human review.
- Source URLs and file paths remain in document and chunk metadata and are
  included in the generated context for evidence review.
- If the retrieved context is insufficient, the draft should say so. Generated
  content remains a draft and requires human approval before publication.

## Alternative considered: direct context injection

Direct injection would be reasonable for a very small, stable corpus: load the
few files, manually choose the relevant passages, and place them directly in
the prompt. It was rejected here because the project already has multiple long
source pages, different request types, separate primary and secondary
evidence, and an expected need to update or extend the source set. Selecting
passages manually for every type of request would make relevance logic harder
to reproduce and maintain. Injecting the complete corpus would also grow
prompt size, latency, and cost even when a request needs only a few passages.

RAG has a real trade-off: embeddings require an additional API call and the
index must be refreshed when source material changes. That cost is accepted in
exchange for request-specific context, clearer scaling, and chunk-level source
traceability.
