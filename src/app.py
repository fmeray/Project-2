"""Gradio UI for grounded FREITAG content generation and human approval."""

import base64
from pathlib import Path

import gradio as gr

from content_delivery import deliver_content
from content_pipeline import save_approved_draft
from llm_integration import generate_text
from prompt_templates import build_prompt, load_template


CHANNELS = ["instagram", "linkedin", "newsletter", "email"]
BACKGROUND_IMAGE = Path(__file__).with_name("FREITAG.png")


def _background_css() -> str:
    """Apply distinct light/dark palettes to the industrial studio layout."""

    return """
    .gradio-container {
        --studio-paper: #f5f2e9;
        --studio-soft: #e6e1d5;
        --studio-field: #ffffff;
        --studio-ink: #101b2c;
        --studio-muted: #4c5868;
        --studio-line: #637080;
        --studio-hover: #d6d0c2;
        --studio-link: #a3380d;
        --studio-overlay: rgba(239, 232, 215, .28);
        --studio-shadow: #101b2c;
        color-scheme: light;
        --body-text-color: var(--studio-ink);
        --body-text-color-subdued: var(--studio-muted);
        --background-fill-primary: var(--studio-paper);
        --background-fill-secondary: var(--studio-soft);
        --block-background-fill: var(--studio-paper);
        --block-border-color: var(--studio-line);
        --block-label-background-fill: var(--studio-paper);
        --block-label-text-color: var(--studio-ink);
        --block-title-text-color: var(--studio-ink);
        --input-background-fill: var(--studio-field);
        --input-border-color: var(--studio-line);
        --input-border-color-focus: var(--studio-ink);
        --input-placeholder-color: var(--studio-muted);
        --input-text-size: 16px;
        --input-radius: 4px;
        --border-color-primary: var(--studio-line);
        --border-color-accent: var(--studio-ink);
        --neutral-50: var(--studio-field);
        --neutral-100: var(--studio-soft);
        --neutral-200: #d9dde1;
        --neutral-500: var(--studio-muted);
        --neutral-700: #28364a;
        --neutral-800: var(--studio-ink);
        --neutral-900: var(--studio-ink);
        --button-primary-background-fill: #ff823f;
        --button-primary-background-fill-hover: #ff9d68;
        --button-primary-text-color: #101722;
        --button-primary-border-color: #101722;
        --button-secondary-background-fill: var(--studio-soft);
        --button-secondary-background-fill-hover: var(--studio-hover);
        --button-secondary-text-color: var(--studio-ink);
        --button-secondary-border-color: var(--studio-line);
        --link-text-color: var(--studio-link);
        --link-text-color-hover: var(--studio-link);
        --body-text-size: 16px;
        --font: Arial, Helvetica, sans-serif;
        font-family: Arial, Helvetica, sans-serif;
        max-width: 1200px !important;
        padding: 32px 24px 48px !important;
        gap: 20px !important;
        position: relative;
        isolation: isolate;
        background: transparent !important;
        color: var(--studio-ink);
    }
    .dark .gradio-container, .gradio-container.dark {
        --studio-paper: #142238;
        --studio-soft: #1d3049;
        --studio-field: #0b1626;
        --studio-ink: #f5f2e9;
        --studio-muted: #b7c4d6;
        --studio-line: #7e91aa;
        --studio-hover: #2e4563;
        --studio-link: #ffad79;
        --studio-overlay: rgba(5, 13, 25, .52);
        --studio-shadow: #000000;
        color-scheme: dark;
    }
    .gradio-container > * {
        position: relative;
        z-index: 1;
    }
    #studio-background {
        position: fixed !important;
        inset: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 0 !important;
        pointer-events: none;
        padding: 0 !important;
        margin: 0 !important;
        border: 0 !important;
        background: #101b2c !important;
    }
    #studio-background img {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    #studio-background::after {
        content: "";
        position: absolute;
        inset: 0;
        background: var(--studio-overlay);
    }
    #studio-photo-window {
        min-height: 180px;
        background: transparent !important;
        border: 0 !important;
        pointer-events: none;
    }
    #studio-header {
        background: #ff823f;
        border: 2px solid #101722;
        border-radius: 0;
        padding: 32px;
        box-shadow: 8px 8px 0 var(--studio-shadow);
        overflow: hidden;
        margin-bottom: 48px;
    }
    #studio-header h1 {
        color: #101722;
        font-size: clamp(40px, 7vw, 88px);
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: -.065em;
        line-height: .98;
        max-width: 850px;
        margin: 12px 0 24px;
    }
    #studio-header p { color: #101722; margin-bottom: 0; line-height: 1.6; max-width: 620px; }
    #studio-header p:first-child {
        font-family: monospace;
        font-size: 12px;
        letter-spacing: .14em;
        font-weight: 700;
    }
    .studio-panel {
        background: var(--studio-paper) !important;
        border: 2px solid var(--studio-line) !important;
        border-radius: 0 !important;
        box-shadow: 6px 6px 0 var(--studio-shadow);
        padding: 24px !important;
        gap: 20px !important;
    }
    .studio-panel .prose, .studio-panel label, .studio-panel .block-title {
        color: var(--studio-ink) !important;
    }
    .studio-panel .prose { line-height: 1.6; }
    .studio-panel input, .studio-panel textarea {
        color: var(--studio-ink) !important;
        background: var(--studio-field) !important;
        caret-color: var(--studio-ink);
    }
    .studio-panel input::placeholder, .studio-panel textarea::placeholder {
        color: var(--studio-muted) !important;
        opacity: 1;
    }
    .gradio-container button { min-height: 50px; font-weight: 800; border-radius: 0 !important; letter-spacing: .025em; }
    .gradio-container :is(button, input, textarea, [tabindex]):focus-visible {
        outline: 3px solid var(--studio-link) !important;
        outline-offset: 3px;
    }
    #studio-status { border-left: 5px solid #ff823f; padding: 16px; background: var(--studio-soft); }
    .studio-section h2 { font-size: 18px; text-transform: uppercase; letter-spacing: .06em; margin: 0; }
    #studio-sources { overflow-wrap: anywhere; }
    @media (max-width: 640px) {
        .gradio-container { padding: 16px 12px 32px !important; }
        .studio-panel, #studio-header { padding: 16px !important; }
    }
    """


def _background_html() -> str:
    """Render the photo as an image instead of relying on a CSS pseudo-element."""

    if not BACKGROUND_IMAGE.exists():
        return ""
    image_data = base64.b64encode(BACKGROUND_IMAGE.read_bytes()).decode("ascii")
    return (
        '<img src="data:image/png;base64,' + image_data + '" alt="" '
        'aria-hidden="true" style="position:fixed;inset:0;width:100vw;'
        'height:100vh;object-fit:cover;pointer-events:none;">'
    )


def _source_summary(documents) -> str:
    if not documents:
        return "No sources retrieved."
    return "\n".join(
        f"- {document.metadata.get('title', document.path)}"
        for document in documents
    )


def generate_draft_ui(request: str, channel: str):
    if not request or not request.strip():
        raise gr.Error("Enter a content request first.")
    # RAG controls retrieval internally; the UI does not expose a file limit.
    prompt = build_prompt(channel, request.strip())
    try:
        draft = generate_text(prompt["system"], prompt["user"])
    except Exception as exc:
        raise gr.Error(str(exc)) from exc
    return (
        draft,
        prompt,
        _source_summary(prompt["documents"]),
        "",
        "",
        "",
        gr.update(value="", visible=False),
        "Draft generated. Review it and add feedback if needed.",
    )


def revise_draft_ui(
    prompt: dict | None,
    draft: str,
    feedback: str,
    request: str,
):
    if not prompt or not draft.strip():
        raise gr.Error("Generate a draft before requesting a revision.")
    if not feedback or not feedback.strip():
        raise gr.Error("Enter feedback, or use Approve & save if the draft is ready.")

    revision_template = load_template("revision")
    revision_prompt = revision_template.format(
        request=request,
        draft=draft,
        feedback=feedback.strip(),
    )
    try:
        revised = generate_text(prompt["system"], revision_prompt)
    except Exception as exc:
        raise gr.Error(str(exc)) from exc
    return (
        revised,
        "",
        "",
        "",
        gr.update(value="", visible=False),
        "Revision generated using the mandatory reviewer feedback.",
    )


def approve_draft_ui(channel: str, draft: str):
    if not draft or not draft.strip():
        raise gr.Error("Generate a draft before approving it.")
    try:
        from content_pipeline import DEFAULT_OUTPUT_DIR

        path = save_approved_draft(draft, channel, DEFAULT_OUTPUT_DIR)
    except Exception as exc:
        raise gr.Error(str(exc)) from exc
    show_recipient = channel in {"email", "newsletter"}
    return (
        draft,
        str(path),
        "Approved draft saved. Enter an email only if you want to deliver it.",
        gr.update(value="", visible=show_recipient),
    )


def deliver_ui(channel: str, approved_draft: str, recipient_email: str):
    if not approved_draft or not approved_draft.strip():
        raise gr.Error("Approve and save a draft before delivering it.")
    recipient_email = recipient_email or ""
    if channel in {"email", "newsletter"} and not recipient_email.strip():
        raise gr.Error("Enter the recipient email for email/newsletter delivery.")
    try:
        result = deliver_content(
            channel,
            approved_draft,
            recipient_email=recipient_email.strip() or None,
        )
    except Exception as exc:
        raise gr.Error(str(exc)) from exc
    return f"Delivered via {result.channel} to {result.destination}. ID: {result.external_id}"


def create_app() -> gr.Blocks:
    with gr.Blocks(title="FREITAG Content Studio") as demo:
        if BACKGROUND_IMAGE.exists():
            gr.HTML(_background_html(), elem_id="studio-background")
        gr.Markdown(
            "STUDIO / FREITAG — HUMAN-REVIEWED CONTENT\n\n"
            "# FREITAG Content Studio\n\n"
            "Generate grounded content, review every revision, and save only "
            "human-approved drafts.",
            elem_id="studio-header",
        )

        gr.HTML("", elem_id="studio-photo-window", min_height=180)

        prompt_state = gr.State(None)
        approved_state = gr.State("")

        with gr.Row():
            with gr.Column(scale=2, min_width=280, elem_classes=["studio-panel"]):
                gr.Markdown("## 01 / The brief", elem_classes=["studio-section"])
                request = gr.Textbox(
                    label="Content request",
                    placeholder="Create a LinkedIn post about FREITAG's circular materials.",
                    lines=4,
                )
                channel = gr.Dropdown(
                    choices=CHANNELS,
                    value="instagram",
                    label="Content channel",
                )
                generate_button = gr.Button("1Generate draft", variant="primary")
            with gr.Column(scale=3, min_width=280, elem_classes=["studio-panel"]):
                gr.Markdown("## 02 / Source desk", elem_classes=["studio-section"])
                status = gr.Markdown("Ready.", elem_id="studio-status")
                sources = gr.Markdown(elem_id="studio-sources")

        with gr.Column(elem_classes=["studio-panel"]):
            gr.Markdown("## 03 / The edit", elem_classes=["studio-section"])
            draft = gr.Textbox(label="Draft for human review", lines=12)
            feedback = gr.Textbox(
                label="Reviewer feedback (mandatory for revision)",
                placeholder="Explain what must change, or leave empty to approve.",
                lines=4,
            )
            with gr.Row():
                revise_button = gr.Button("Rewrite with feedback", variant="secondary")
                approve_button = gr.Button("Approve & save", variant="primary")
                deliver_button = gr.Button("Deliver approved content")

            saved_path = gr.Textbox(label="Approved draft path", interactive=False)
            recipient_email = gr.Textbox(
                label="Recipient email (optional; enter after approval)",
                placeholder="recipient@example.com",
                visible=False,
            )
            delivery_status = gr.Textbox(label="Delivery status", interactive=False)
            gr.Markdown(
                "Delivery is disabled unless `CONTENT_DELIVERY_ENABLED=true` is set "
                "and the selected channel credentials are configured in `.env`."
            )

        generate_button.click(
            generate_draft_ui,
            inputs=[request, channel],
            outputs=[
                draft,
                prompt_state,
                sources,
                approved_state,
                saved_path,
                delivery_status,
                recipient_email,
                status,
            ],
        )
        revise_button.click(
            revise_draft_ui,
            inputs=[prompt_state, draft, feedback, request],
            outputs=[
                draft,
                approved_state,
                saved_path,
                delivery_status,
                recipient_email,
                status,
            ],
        )
        approve_button.click(
            approve_draft_ui,
            inputs=[channel, draft],
            outputs=[approved_state, saved_path, status, recipient_email],
        )
        deliver_button.click(
            deliver_ui,
            inputs=[channel, approved_state, recipient_email],
            outputs=delivery_status,
        )
    return demo


if __name__ == "__main__":
    create_app().launch(css=_background_css())
