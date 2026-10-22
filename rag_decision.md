# RAG decision

## Decision

Use retrieval-augmented generation (RAG) for the FREITAG content creator.

## Rationale

1. **Grounding:** product and brand content must use approved company material
   rather than relying only on general model knowledge.
2. **Traceability:** source paths can be included with the context so reviewers
   can check claims before publication.
3. **Maintainability:** Markdown sources can be updated without retraining a
   model or embedding company facts directly in application code.
4. **Scope:** a local Markdown-based approach is practical for the two-day sprint
   and leaves automated publishing and live monitoring for later.

The model remains responsible for drafting and formatting, while source owners
and human reviewers remain responsible for factual and legal approval.
