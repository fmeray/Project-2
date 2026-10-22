# Project structure and stakeholder analysis

## 1. Project identity and objectives

| Field | Definition |
| --- | --- |
| Project | FREITAG AI Content Creator |
| Goal | Create multi-channel marketing content for FREITAG, including LinkedIn, newsletters, and X. |
| Project type | Marketing / AI-assisted content production |
| Timeline | 22–23 October 2026 |
| Quality objective | Produce well-structured, platform-appropriate content tailored to the audience and grounded in company data. |
| Time objective | Fetch, process, and use the approved data within two working days. |
| Cost objective | Track LLM/API usage and keep calls within the agreed project budget. |

The project has a defined goal, limited time and resources, cross-functional
dependencies, responsibility for the quality of its results, and a defined start and
end date.

## 2. Project purpose

This project delivers a small, reproducible retrieval-augmented generation (RAG)
pipeline for FREITAG's multi-channel content creation. The pipeline ingests a
primary and a secondary Markdown knowledge base, selects relevant context, calls an
LLM, and returns content with enough evidence for a reviewer to distinguish it from
a generic ChatGPT response.

The structure below is the target structure for the `ai-content-creator` project.
The repository currently contains only `README.md` and this document, so the paths
listed in the requirements table describe the agreed implementation structure.

## 3. Proposed repository structure

```text
ai-content-creator/
├── src/
│   ├── document_processor.py       # Markdown ingestion and processing
│   ├── knowledge_base.py           # Primary and secondary KB management
│   ├── prompt_templates.py         # Advanced prompt templates
│   ├── content_pipeline.py         # Document → retrieve → iterate
│   ├── llm_integration.py          # LLM API integration
│   └── main.py                     # Main entry point
├── knowledge_base/
│   ├── primary/                    # Company documents (Markdown)
│   │   ├── brand_guidelines.md
│   │   ├── product_specs.md
│   │   └── past_content/
│   └── secondary/                  # Industry research (Markdown)
│       ├── market_trends.md
│       └── competitor_analysis.md
├── templates/                      # Prompt templates
├── requirements.txt
├── README.md
├── agents.md                       # Required coding-agent rules
├── project_structure.md            # Required project-management kickoff
├── rag_decision.md                 # Required RAG choice and defence
└── .env                            # API keys; never commit this file
```

### Directory responsibilities

| Location | Responsibility |
| --- | --- |
| `src/document_processor.py` | Load, validate, normalize, and process Markdown documents. |
| `src/knowledge_base.py` | Manage primary and secondary knowledge-base sources and metadata. |
| `knowledge_base/primary/` | Authoritative FREITAG company Markdown, including brand guidelines, product specifications, and past content. |
| `knowledge_base/secondary/` | Supplementary industry research, including market trends and competitor analysis. |
| `src/prompt_templates.py` and `templates/` | Define and store reusable prompt templates. |
| `src/content_pipeline.py` | Orchestrate document processing, retrieval, content generation, and iteration. |
| `src/llm_integration.py` | Encapsulate LLM API calls, configuration, and error handling. |
| `src/main.py` | Provide the main end-to-end application entry point. |
| `requirements.txt` | Declare Python dependencies needed to run the project. |
| `agents.md` | Define coding-agent rules and implementation guidance. |
| `rag_decision.md` | Explain and defend the decision to use RAG. |
| `.env` | Store local API keys and configuration; exclude it from version control. |

## 4. Stakeholder analysis

### 4.1 Stakeholder map

| Stakeholder | Interest / success criteria | Influence | Main concerns | Engagement / response |
| --- | --- | --- | --- | --- |
| Marketing & E-commerce team | Publish useful, on-brand content that supports marketing and sales goals. | High | Off-brand tone, weak platform fit, inaccurate product claims. | Approve the content brief, review sample outputs, and validate channel suitability. |
| Client / FREITAG brand team | Protect the brand identity and ensure content reflects approved company information. | High | Misrepresentation, unsupported claims, or misuse of brand assets. | Act as primary knowledge-base owner and approve final content before publication. |
| Business owner / project evaluator | Deliver all mandatory requirements within the two-day scope and budget. | High | Missing evidence, scope creep, and unclear project value. | Monitor the requirement matrix, accept the final demonstration, and review API usage. |
| Business partners / channel owners | Receive content that is usable for their channel and audience. | Medium | Incorrect formats, timing, or calls to action. | Confirm channel constraints and provide feedback on representative drafts. |
| Legal / privacy reviewer | Ensure marketing claims, data use, and AI-assisted content meet applicable rules. | High | Unapproved claims, confidential data exposure, or non-compliant publishing. | Review source material and high-risk outputs; require human approval before publication. |
| Developer / maintainer | Keep the pipeline modular, testable, and reproducible. | High | Hard-coded prompts, hidden dependencies, and undocumented setup. | Maintain the implementation, tests, `agents.md`, and runbook. |
| LLM/API provider | Receive valid requests and remain within service and quota limits. | Medium | Invalid requests, quota failures, or unavailable service. | Centralize the client, handle failures clearly, and document required environment variables. |

### 4.2 Stakeholder priorities and decisions

1. The subject-matter expert's primary knowledge base is the highest-priority source.
   Secondary material can add context but must not silently contradict the primary
   source.
2. The end user's trust is supported by showing the source document or passage used
   in the answer and by stating when the knowledge base does not contain enough
   evidence.
3. The evaluator's reproducibility requirement is met through one documented
   command, deterministic sample questions where practical, and tests that do not
   require a live LLM for every unit test.
4. The security reviewer's concerns are addressed by keeping credentials out of the
   repository and documenting configuration without recording secret values.

### 4.3 Acceptance questions

- Can a new user identify where both knowledge bases live and run the pipeline from
  the README?
- Can an evaluator verify that retrieved context came from the supplied Markdown?
- Can the maintainer replace a prompt or the LLM client without rewriting the whole
  pipeline?
- Does the evidence show a meaningful difference between a grounded answer and a
  generic ChatGPT answer?

## 5. Requirements and verification matrix

| ID | Must requirement | Maps to (file / module) | How we verify |
| --- | --- | --- | --- |
| M1 | Ingest primary KB Markdown | `src/document_processor.py`, `src/knowledge_base.py` + `knowledge_base/primary/` | Run the application with primary documents and verify that `brand_guidelines.md`, `product_specs.md`, and files in `past_content/` are loaded, normalized, and identified as primary sources. |
| M2 | Ingest secondary KB Markdown | `src/document_processor.py`, `src/knowledge_base.py` + `knowledge_base/secondary/` | Run ingestion with secondary documents and verify that `market_trends.md` and `competitor_analysis.md` are loaded and identified as secondary sources. |
| M3 | Call LLM with KB context | `src/content_pipeline.py`, `src/llm_integration.py`, `src/knowledge_base.py` | Use a mocked LLM call or request log to verify that retrieved passages from the knowledge base are included in the prompt sent to the model. |
| M4 | Reusable prompt templates (≥2) | `src/prompt_templates.py` + `templates/` | Confirm at least two templates are stored in `templates/`, can be selected through `prompt_templates.py`, and render correctly with document context and channel information. |
| M5 | End-to-end pipeline command | `src/main.py`, `src/content_pipeline.py`, `requirements.txt`, `.env` | Follow the README setup instructions and run the main entry point with a sample content request; verify processing, LLM integration, and generated output complete successfully. |
| M6 | Uniqueness evidence vs ChatGPT | `README.md`, `src/content_pipeline.py`, `knowledge_base/primary/` and `knowledge_base/secondary/` | Run the same content request with and without the supplied knowledge base; document at least three grounded FREITAG-specific differences, including source-supported claims or brand details. |
| M7 | RAG decision documented | `rag_decision.md` | `rag_decision.md` states the choice and evaluates at least three criteria, such as grounding, source traceability, and maintainability. |
| M8 | Project structured + agents guided | `project_structure.md`, `agents.md`, `README.md` | The documented tree matches the repository, `agents.md` gives implementation guidance, and a reviewer can follow the documented workflow from the README. |

## 6. Risks

Strategies: **Avoidance** | **Reduction** | **Mitigation** | **Transfer** | **Acceptance**

| Risk | P (L/M/H) | I (L/M/H) | Strategy | Concrete action |
| --- | --- | --- | --- | --- |
| Generated content makes unsupported or off-brand claims | M | H | Reduction | Restrict prompts to retrieved FREITAG sources, show source context, and require Marketing/Client review before publication. |
| LLM API outage, quota limit, or unexpected API cost | M | M | Mitigation | Load credentials from `.env`, handle API failures with a clear message, track token usage, and keep a manual review fallback. |
| Confidential information or API keys are exposed | L | H | Avoidance | Exclude `.env` from version control, use only approved Markdown sources, and avoid logging secrets or sensitive prompt content. |



