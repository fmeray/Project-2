# RAG decision

## Decision

Use direct context injection strategy for the FREITAG content creator.

## Rationale

For the FREITAG AI Content Creator, we will use a direct context injection strategy rather than a vector-based RAG retrieval system. This approach is optimal because our knowledge base consists of a small, highly curated set of static Markdown files that rarely change. Given the two-day development window, building a full vector retrieval pipeline introduces unnecessary complexity; instead, injecting the relevant product and brand guidelines directly into the prompt ensures maximum accuracy, lower latency, and guaranteed source traceability without exceeding the LLM's context window.
