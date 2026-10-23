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
    """Embed the local FREITAG image so Gradio can serve it reliably."""

    if not BACKGROUND_IMAGE.exists():
        return ""
    image_data = base64.b64encode(BACKGROUND_IMAGE.read_bytes()).decode("ascii")
    return f"""
    .gradio-container {{
        background: transparent !important;
        background-color: transparent !important;
        max-width: 1400px !important;
        position: relative !important;
        z-index: 1 !important;
    }}

    #freitag-background {{
        position: fixed !important;
        inset: 0 !important;
        z-index: 0 !important;
        pointer-events: none !important;
        background-color: #242424 !important;
        background-image:
            linear-gradient(rgba(0, 0, 0, 0.48), rgba(0, 0, 0, 0.48)),
            url("data:image/png;base64,{image_data}") !important;
        background-position: center !important;
        background-size: cover !important;
        background-repeat: no-repeat !important;
    }}

    .gradio-container .block,
    .gradio-container .gr-box,
    .gradio-container .gr-panel {{
        background: rgba(255, 255, 255, 0.91) !important;
        border-color: rgba(255, 255, 255, 0.7) !important;
    }}
    """


def _background_html() -> str:
    """Create a fixed in-app background layer using the local image."""

    if not BACKGROUND_IMAGE.exists():
        return ""
    image_data = base64.b64encode(BACKGROUND_IMAGE.read_bytes()).decode("ascii")
    return (
        '<div id="freitag-background" '
        'style="position:fixed;inset:0;z-index:0;pointer-events:none;'
        'background-color:#242424;'
        'background-image:linear-gradient(rgba(0,0,0,.48),rgba(0,0,0,.48)),'
        f'url(data:image/png;base64,{image_data});'
        'background-position:center;background-size:cover;background-repeat:no-repeat;">'
        "</div>"
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
            gr.HTML(_background_html())
        gr.Markdown(
            "# FREITAG Content Studio\n"
            "Generate grounded content, review every revision, and save only "
            "human-approved drafts."
        )

        prompt_state = gr.State(None)
        approved_state = gr.State("")

        with gr.Row():
            with gr.Column(scale=2):
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
                generate_button = gr.Button("1. Generate draft", variant="primary")
            with gr.Column(scale=3):
                status = gr.Markdown("Ready.")
                sources = gr.Markdown()

        draft = gr.Textbox(label="Draft for human review", lines=12)
        feedback = gr.Textbox(
            label="Reviewer feedback (mandatory for revision)",
            placeholder="Explain what must change, or leave empty to approve.",
            lines=4,
        )
        with gr.Row():
            revise_button = gr.Button("2. Rewrite with feedback", variant="secondary")
            approve_button = gr.Button("3. Approve & save", variant="primary")
            deliver_button = gr.Button("4. Deliver approved content")

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
