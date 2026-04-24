from __future__ import annotations

import html
import json
import random
from pathlib import Path

import gradio as gr

from tutor.adaptive import choose_next_item, init_mastery, update_mastery
from tutor.asr_adapt import OfflineASRService, asr_status_snapshot
from tutor.curriculum_loader import load_curriculum
from tutor.dashboard import (
    export_results_bundle,
    export_results_card,
    learner_dashboard_html,
    system_dashboard_html,
)
from tutor.language import choose_reply_language, detect_language, localized_stem
from tutor.lora_language import LoRALanguageHead
from tutor.report_logic import build_weekly_report, render_parent_report_html
from tutor.scoring import score_response
from tutor.storage import (
    dashboard_snapshot,
    get_or_create_learner,
    init_db,
    learner_attempt_summary,
    list_learners,
    load_mastery,
    load_recent_item_ids,
    recent_attempts,
    save_attempt,
    save_mastery,
)
from tutor.visual_tasks import render_visual_html


# Project paths are defined once here so the rest of the file reads like app logic.
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUTS_DIR = ROOT / "outputs"
DB_PATH = DATA_DIR / "local_store.sqlite"
SCHEMA_PATH = DATA_DIR / "seed" / "parent_report_schema.json"
KT_METRICS_PATH = OUTPUTS_DIR / "kt_metrics.json"
ASR_MODEL_DIR = ROOT / "models" / "asr"
LORA_ADAPTER_DIR = ROOT / "models" / "lora_numeracy_adapter"
LORA_METADATA_PATH = LORA_ADAPTER_DIR / "adapter_metadata.json"
CURRICULUM = load_curriculum(DATA_DIR)

# The learner database is created on first run.
init_db(DB_PATH)

# If local models have already been prepared, the app picks them up automatically.
asr_service = OfflineASRService(str(ASR_MODEL_DIR) if ASR_MODEL_DIR.exists() else None)
if LORA_METADATA_PATH.exists():
    metadata = json.loads(LORA_METADATA_PATH.read_text(encoding="utf-8"))
    lora_service = LoRALanguageHead(
        base_model=metadata.get("base_model"),
        adapter_path=metadata.get("adapter_path"),
    )
else:
    lora_service = LoRALanguageHead()


def learner_choices() -> list[str]:
    return [f"{name} [{learner_id}]" for learner_id, name in list_learners(DB_PATH)]


def parse_learner_choice(raw: str) -> tuple[str | None, str | None]:
    if not raw or "[" not in raw or "]" not in raw:
        return None, None
    name, tail = raw.rsplit("[", 1)
    return tail[:-1], name.strip()


def build_options(answer: int, item_id: str) -> list[str]:
    rng = random.Random(item_id)
    options = {answer}
    while len(options) < 4:
        candidate = max(0, answer + rng.choice([-3, -2, -1, 1, 2, 3, 4]))
        options.add(candidate)
    out = [str(value) for value in sorted(options)]
    rng.shuffle(out)
    return out


def prompt_card(item: dict, preferred_language: str) -> str:
    reply_language = choose_reply_language(preferred_language, preferred_language)
    prompt = localized_stem(item, reply_language)
    answer = item["answer_int"]
    skill = item["skill"].replace("_", " ").title()
    difficulty = item.get("difficulty", 1)
    return f"""
    <div class="hero-card">
      <div class="eyebrow">Current skill: {skill} - Difficulty {difficulty}</div>
      <div class="prompt-text">{prompt}</div>
      {render_visual_html(item)}
      <div class="hint-line">Tap an answer, type a number word, or use the microphone. Correct answer stored for evaluation: {answer}.</div>
    </div>
    """


def feedback_card(message: str, positive: bool = True, title: str = "Tutor feedback") -> str:
    tone = "#2a9d8f" if positive else "#d95f5f"
    background = "#ecf8f4" if positive else "#fff1ef"
    safe_title = html.escape(title)
    safe_message = html.escape(message)
    return (
        f"<div style='border-left:5px solid {tone};background:{background};padding:12px 14px;border-radius:12px'>"
        f"<div style='font-weight:700;margin-bottom:6px'>{safe_title}</div>"
        f"<div>{safe_message}</div>"
        "</div>"
    )


def scenario_card() -> str:
    return """
    <div class="panel-card">
      <h3>First 90 seconds</h3>
      <ol>
        <li>The child hears a warm greeting in Kinyarwanda first.</li>
        <li>The screen shows one clear visual counting task with four large answer buttons.</li>
        <li>If the child stays silent for 10 seconds, the tutor repeats the prompt slowly and highlights the tap buttons.</li>
        <li>The tutor rewards correct answers immediately with short praise and simple next-step guidance.</li>
      </ol>
    </div>
    """


def deployment_card() -> str:
    return """
    <div class="panel-card">
      <h3>Shared tablet deployment</h3>
      <ul>
        <li>Each child has a local learner profile on one device.</li>
        <li>Progress stays in local SQLite and survives reboot.</li>
        <li>Learners switch through a simple picker instead of email or password.</li>
        <li>Any future sync should send only aggregated weekly statistics.</li>
      </ul>
    </div>
    """


def build_model_status() -> dict:
    asr_state = asr_status_snapshot(str(ASR_MODEL_DIR) if ASR_MODEL_DIR.exists() else None)
    lora_state = lora_service.status()
    return {
        "asr": asr_state["message"],
        "adaptation": "Pitch, tempo, and classroom-noise augmentation is implemented in scripts/adapt_child_asr.py.",
        "lora": lora_state["message"],
        "offline": "Tutor runtime uses only local curriculum, local storage, and optional local model folders.",
    }


def refresh_system_dashboard() -> str:
    return system_dashboard_html(dashboard_snapshot(DB_PATH), KT_METRICS_PATH, build_model_status())


def learner_panels(learner_id: str, learner_name: str) -> tuple[str, str]:
    report = build_weekly_report(DB_PATH, learner_id, SCHEMA_PATH)
    summary = learner_attempt_summary(DB_PATH, learner_id)
    attempts = recent_attempts(DB_PATH, learner_id, limit=12)
    return render_parent_report_html(report), learner_dashboard_html(learner_name, summary, attempts)


def export_views(learner_name: str, report_html: str, learner_html: str, system_html: str) -> tuple[str, str]:
    bundle = export_results_bundle(OUTPUTS_DIR, learner_name, report_html, learner_html, system_html)
    return export_results_card(bundle), str(bundle["results_bundle"])


# This state object travels between button clicks so the tutor can continue the same learner session.
def make_state(
    learner_id: str,
    learner_name: str,
    preferred_language: str,
    mastery: dict[str, float],
    item: dict,
    recent_ids: list[str],
) -> dict:
    return {
        "learner_id": learner_id,
        "learner_name": learner_name,
        "preferred_language": preferred_language,
        "mastery": mastery,
        "current_item": item,
        "recent_ids": recent_ids,
    }


def session_banner(learner_name: str, preferred_language: str) -> str:
    language_names = {"kin": "Kinyarwanda", "en": "English", "fr": "French"}
    return f"""
    <div class="banner-card">
      <div><b>Learner:</b> {learner_name}</div>
      <div><b>Tutor language:</b> {language_names.get(preferred_language, preferred_language)}</div>
      <div><b>Mode:</b> Offline adaptive tutor with tap and microphone response</div>
    </div>
    """


def item_question_text(item: dict, preferred_language: str) -> str:
    reply_language = choose_reply_language(preferred_language, preferred_language)
    return localized_stem(item, reply_language)


def answer_label(raw_response: str, parsed: int | None) -> str:
    if parsed is not None:
        return str(parsed)
    if raw_response.strip():
        return raw_response.strip()
    return "no answer"


def start_session(learner_name: str, learner_choice: str, preferred_language: str):
    # Start a new learner or switch to an existing learner, then refresh the app and HTML dashboard.
    preferred_language = (preferred_language or "kin").lower()
    existing_id, existing_name = parse_learner_choice(learner_choice)
    if existing_id:
        learner_id = existing_id
        learner_name = existing_name or learner_name or "Learner"
        mastery = load_mastery(DB_PATH, learner_id) or init_mastery()
    else:
        learner_id, learner_name = get_or_create_learner(DB_PATH, learner_name or "Learner", preferred_language, init_mastery())
        mastery = load_mastery(DB_PATH, learner_id) or init_mastery()

    recent_ids = load_recent_item_ids(DB_PATH, learner_id)
    item = choose_next_item(CURRICULUM, mastery, recent_ids)
    options = build_options(int(item["answer_int"]), item["id"])
    state = make_state(learner_id, learner_name, preferred_language, mastery, item, recent_ids + [item["id"]])

    report_html, learner_html = learner_panels(learner_id, learner_name)
    system_html = refresh_system_dashboard()
    export_html, export_file = export_views(learner_name, report_html, learner_html, system_html)
    asr_status = asr_service.status()["message"]

    return (
        session_banner(learner_name, preferred_language),
        prompt_card(item, preferred_language),
        gr.update(choices=options, value=None),
        "",
        feedback_card(
            "The first question is shown above. After each answer, this box will explain the last question while the next one loads.",
            positive=True,
            title="Session ready",
        ),
        report_html,
        learner_html,
        system_html,
        export_html,
        export_file,
        f"ASR status: {asr_status}",
        state,
        gr.update(choices=learner_choices(), value=f"{learner_name} [{learner_id}]"),
    )


def transcribe_microphone(audio_blob, state: dict):
    if not state or not state.get("current_item"):
        return "", "Start a learner session before using the microphone."
    result = asr_service.transcribe(audio_blob, preferred_language=state.get("preferred_language", "kin"))
    if result["text"]:
        return result["text"], result["message"]
    return "", result["message"]


def submit_answer(choice: str, typed_answer: str, state: dict):
    # Score the answer, update the learner model, and rewrite the standalone HTML dashboard.
    if not state or not state.get("current_item"):
        return (
            "",
            "",
            gr.update(),
            "",
            feedback_card("Start a learner session first.", positive=False, title="Action needed"),
            "",
            "",
            refresh_system_dashboard(),
            "",
            None,
            "ASR status will appear here.",
            state,
            gr.update(),
        )

    item = state["current_item"]
    question_text = item_question_text(item, state["preferred_language"])
    raw_response = typed_answer.strip() if typed_answer and typed_answer.strip() else choice
    correct, parsed = score_response(item, raw_response)
    detected = detect_language(raw_response or "")
    reply_language = choose_reply_language(state["preferred_language"], detected)

    mastery = update_mastery(state["mastery"], item["skill"], correct)
    save_mastery(DB_PATH, state["learner_id"], mastery)
    save_attempt(DB_PATH, state["learner_id"], item["id"], item["skill"], correct, raw_response or "", parsed, detected)

    feedback_payload = lora_service.generate_feedback(item, correct, reply_language)
    feedback_text = (
        f"Previous question: {question_text} "
        f"Your answer: {answer_label(raw_response or '', parsed)}. "
        f"{feedback_payload['text']} "
        f"Response language detected: {detected or 'unknown'}. "
        "A new question is now shown above."
    )
    if feedback_payload.get("error"):
        feedback_text += " Template feedback was used because the tiny local text model was not confident enough."

    recent_ids = (state.get("recent_ids") or [])[-5:] + [item["id"]]
    next_item = choose_next_item(CURRICULUM, mastery, recent_ids)
    options = build_options(int(next_item["answer_int"]), next_item["id"])

    state["mastery"] = mastery
    state["current_item"] = next_item
    state["recent_ids"] = recent_ids + [next_item["id"]]

    report_html, learner_html = learner_panels(state["learner_id"], state["learner_name"])
    system_html = refresh_system_dashboard()
    export_html, export_file = export_views(state["learner_name"], report_html, learner_html, system_html)
    asr_status = asr_service.status()["message"]

    return (
        session_banner(state["learner_name"], state["preferred_language"]),
        prompt_card(next_item, state["preferred_language"]),
        gr.update(choices=options, value=None),
        "",
        feedback_card(feedback_text, positive=correct, title="Previous answer result"),
        report_html,
        learner_html,
        system_html,
        export_html,
        export_file,
        f"ASR status: {asr_status}",
        state,
        gr.update(choices=learner_choices(), value=f"{state['learner_name']} [{state['learner_id']}]"),
    )


CUSTOM_CSS = """
body, .gradio-container {background:#f4f7f8 !important; font-family:Arial,Helvetica,sans-serif}
.app-shell {max-width:1400px;margin:0 auto}
.hero-card {background:#ffffff;border:1px solid #dce5ea;border-radius:18px;padding:18px}
.eyebrow {font-size:12px;color:#60707d;margin-bottom:8px;text-transform:uppercase;letter-spacing:.04em}
.prompt-text {font-size:28px;font-weight:700;line-height:1.3;margin-bottom:14px;color:#17212b}
.hint-line {margin-top:10px;color:#60707d;font-size:13px}
.banner-card {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;background:#0f3d45;color:#f7fbfc;padding:14px 16px;border-radius:16px}
.panel-card {background:#ffffff;border:1px solid #dce5ea;border-radius:14px;padding:16px}
"""


# Build the child-facing app with clear tabs for tutoring, reporting, and the single exported HTML dashboard.
with gr.Blocks(title="Early Math Tutor Offline") as demo:
    app_state = gr.State({})
    gr.Markdown(
        """
        <div class="app-shell">
          <h1 style="margin-bottom:4px">Early Math Tutor Offline</h1>
          <p style="margin-top:0;color:#60707d">Offline early numeracy tutor with adaptive practice, optional microphone input, learner dashboards, and parent-ready reporting.</p>
        </div>
        """
    )

    with gr.Row():
        learner_name = gr.Textbox(label="New learner name", placeholder="Type learner name")
        learner_picker = gr.Dropdown(label="Existing learner", choices=learner_choices(), allow_custom_value=False)
        preferred_language = gr.Dropdown(label="Tutor language", choices=["kin", "en", "fr"], value="kin")
        start_btn = gr.Button("Start or switch learner", variant="primary")

    status_html = gr.HTML(session_banner("No learner yet", "kin"))

    with gr.Tabs():
        with gr.Tab("Tutor"):
            with gr.Row():
                with gr.Column(scale=7):
                    prompt_html = gr.HTML(scenario_card())
                    choice = gr.Radio(label="Tap an answer", choices=[])
                    typed_answer = gr.Textbox(label="Typed or spoken-word answer", placeholder="e.g. five, cinq, esheshatu, 6")
                    with gr.Row():
                        submit_btn = gr.Button("Submit answer", variant="primary")
                        clear_btn = gr.Button("Clear answer")
                    feedback_html = gr.HTML(
                        feedback_card(
                            "The first activity will appear here after you start a learner session.",
                            positive=True,
                            title="Tutor feedback",
                        )
                    )
                with gr.Column(scale=5):
                    gr.Markdown("### Microphone response")
                    mic = gr.Audio(label="Record child answer", sources=["microphone"], type="numpy")
                    use_mic_btn = gr.Button("Transcribe microphone")
                    asr_status = gr.Markdown("ASR status will appear here.")
                    gr.HTML(deployment_card())

        with gr.Tab("Parent Report"):
            report_html = gr.HTML(
                "<p style='color:#60707d'>The weekly parent report preview appears here after a learner starts answering items.</p>"
            )

        with gr.Tab("Learner Dashboard"):
            learner_html = gr.HTML(
                "<p style='color:#60707d'>Learner progress dashboard appears here after attempts are saved.</p>"
            )

        with gr.Tab("System Dashboard"):
            system_html = gr.HTML(refresh_system_dashboard())

        with gr.Tab("HTML Results"):
            html_exports = gr.HTML(
                "<p style='color:#60707d'>Start a learner session to generate one standalone HTML dashboard in the outputs folder.</p>"
            )
            export_file = gr.File(label="Generated HTML dashboard", file_count="single")

    start_btn.click(
        start_session,
        inputs=[learner_name, learner_picker, preferred_language],
        outputs=[
            status_html,
            prompt_html,
            choice,
            typed_answer,
            feedback_html,
            report_html,
            learner_html,
            system_html,
            html_exports,
            export_file,
            asr_status,
            app_state,
            learner_picker,
        ],
    )
    use_mic_btn.click(
        transcribe_microphone,
        inputs=[mic, app_state],
        outputs=[typed_answer, asr_status],
    )
    submit_btn.click(
        submit_answer,
        inputs=[choice, typed_answer, app_state],
        outputs=[
            status_html,
            prompt_html,
            choice,
            typed_answer,
            feedback_html,
            report_html,
            learner_html,
            system_html,
            html_exports,
            export_file,
            asr_status,
            app_state,
            learner_picker,
        ],
    )
    clear_btn.click(lambda: "", outputs=[typed_answer])


if __name__ == "__main__":
    demo.launch(css=CUSTOM_CSS)
