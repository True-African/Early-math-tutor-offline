from __future__ import annotations

import html
import json
import os
from pathlib import Path
from urllib.parse import quote


LANGUAGE_TAGS = {
    "kin": "rw-RW",
    "en": "en-US",
    "fr": "fr-FR",
}

SKILL_LABELS = {
    "counting": "Counting",
    "number_sense": "Number Sense",
    "addition": "Addition",
    "subtraction": "Subtraction",
    "word_problem": "Word Problem",
}

SKILL_KINYARWANDA = {
    "counting": "kubara",
    "number_sense": "gusobanukirwa imibare",
    "addition": "guteranya",
    "subtraction": "gukuramo",
    "word_problem": "ibibazo by'amagambo",
}

SKILL_SYMBOLS = {
    "counting": "123",
    "number_sense": "#",
    "addition": "+",
    "subtraction": "-",
    "word_problem": "?",
}

_PIXEL_GIF = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="


def voice_language_tag(preferred_language: str) -> str:
    return LANGUAGE_TAGS.get((preferred_language or "kin").lower(), "en-US")


def skill_label(skill: str) -> str:
    return SKILL_LABELS.get(skill, skill.replace("_", " ").title())


def skill_symbol(skill: str) -> str:
    return SKILL_SYMBOLS.get(skill, "*")


def _speak_js(message: str, language_tag: str, rate: float = 0.9, pitch: float = 1.0) -> str:
    payload = json.dumps(message)
    lang = json.dumps(language_tag)
    return (
        "(()=>{"
        "if(!('speechSynthesis' in window)){return;}"
        "window.speechSynthesis.cancel();"
        f"const utterance=new SpeechSynthesisUtterance({payload});"
        f"utterance.lang={lang};"
        f"utterance.rate={rate};"
        f"utterance.pitch={pitch};"
        "window.speechSynthesis.speak(utterance);"
        "})()"
    )


def voice_button_html(
    message: str,
    language_tag: str,
    label: str,
    *,
    autoplay: bool = False,
    detail: str = "",
    button_class: str = "voice-btn",
) -> str:
    js = html.escape(_speak_js(message, language_tag), quote=True)
    detail_html = f"<div class='voice-detail'>{html.escape(detail)}</div>" if detail else ""
    autoplay_html = ""
    if autoplay:
        autoplay_html = (
            f"<img alt='' src='{_PIXEL_GIF}' style='display:none' onload=\"{js}\">"
        )
    return f"""
    <div class="voice-box">
      <button type="button" class="{button_class}" onclick="{js}">{html.escape(label)}</button>
      {detail_html}
      {autoplay_html}
    </div>
    """


def build_child_greeting(learner_name: str, question_kin: str, question_en: str) -> str:
    return (
        f"Muraho {learner_name}. Reka tubare hamwe. {question_kin}. "
        f"Hello {learner_name}. Let's count together. {question_en}. Tap the matching number."
    )


def build_silence_support(learner_name: str, question_kin: str, question_en: str) -> str:
    return (
        f"Nta kibazo {learner_name}. Reka nongere mbivuge gahoro. {question_kin}. "
        f"That is okay. Let's try together. {question_en}. Tap the matching number."
    )


def build_parent_voice_summary(report: dict) -> str:
    skills = report.get("skills", {})
    ranked = sorted(skills.items(), key=lambda item: item[1].get("current", 0.0), reverse=True)
    strongest = ranked[0][0] if ranked else "counting"
    weakest = ranked[-1][0] if ranked else "counting"
    learner_name = report.get("learner_name", "umwana")
    sessions = report.get("sessions", 0)
    return (
        f"Muraho mubyeyi. Muri iki cyumweru, {learner_name} yakoze inshuro {sessions} zo kwiga. "
        f"Yitwaye neza cyane muri {SKILL_KINYARWANDA.get(strongest, strongest)}. "
        f"Akeneye kongera gufashwa muri {SKILL_KINYARWANDA.get(weakest, weakest)}. "
        "Mumushimire ako kanya, hanyuma mubare ibintu bitanu byo mu rugo hamwe uyu munsi."
    )


def space_public_base_url() -> str:
    host = (os.environ.get("SPACE_HOST") or "").strip()
    if host:
        return f"https://{host}"
    space_id = (os.environ.get("SPACE_ID") or "").strip()
    if space_id and "/" in space_id:
        return f"https://{space_id.lower().replace('/', '-')}.hf.space"
    return ""


def gradio_file_route(path: Path, app_root: Path) -> str:
    relative = path.relative_to(app_root).as_posix()
    return f"/gradio_api/file={quote(relative, safe='/')}"


def public_file_url(path: Path, app_root: Path) -> str:
    base = space_public_base_url()
    if not base:
        return ""
    return f"{base}{gradio_file_route(path, app_root)}"


def qr_image_html(url: str, label: str) -> str:
    if not url:
        return (
            "<div class='qr-card qr-fallback'>"
            "<div class='qr-title'>Phone replay</div>"
            "<div class='qr-copy'>QR appears automatically in the Hugging Face Space.</div>"
            "</div>"
        )
    encoded = quote(url, safe="")
    return f"""
    <div class="qr-card">
      <div class="qr-title">{html.escape(label)}</div>
      <img src="https://quickchart.io/qr?size=170&text={encoded}" alt="QR code for voice summary" class="qr-image">
      <div class="qr-copy">Scan to hear the short summary on a phone.</div>
    </div>
    """


def write_voice_summary_page(
    output_dir: Path,
    learner_id: str,
    week_starting: str,
    learner_name: str,
    summary_text: str,
    language_tag: str,
) -> Path:
    safe_name = "".join(char.lower() if char.isalnum() else "-" for char in learner_name).strip("-") or learner_id
    page_dir = output_dir / "voice"
    page_dir.mkdir(parents=True, exist_ok=True)
    page_path = page_dir / f"{safe_name}-{week_starting}.html"
    speak_panel = voice_button_html(
        summary_text,
        language_tag,
        "Play summary",
        autoplay=True,
        detail="This page speaks the weekly summary out loud as soon as it opens.",
    )
    page_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Weekly Voice Summary</title>
  <style>
    body {{ margin: 0; background: #f6efe4; font-family: Arial, Helvetica, sans-serif; color: #1b2a2f; }}
    .page {{ max-width: 560px; margin: 0 auto; padding: 28px 18px; }}
    .card {{ background: #ffffff; border: 2px solid #ead7bb; border-radius: 28px; padding: 24px; box-shadow: 0 16px 36px rgba(15, 61, 69, 0.12); }}
    .eyebrow {{ font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: #9a6a2f; margin-bottom: 10px; }}
    h1 {{ margin: 0 0 10px; font-size: 34px; }}
    p {{ font-size: 18px; line-height: 1.5; }}
    .voice-btn {{ border: 0; border-radius: 999px; background: #ef6c2f; color: #fff; font-weight: 700; padding: 14px 22px; font-size: 18px; cursor: pointer; }}
    .voice-detail {{ margin-top: 10px; color: #5b6670; font-size: 14px; }}
  </style>
</head>
<body>
  <div class="page">
    <div class="card">
      <div class="eyebrow">Weekly parent audio</div>
      <h1>{html.escape(learner_name)}</h1>
      <p>{html.escape(summary_text)}</p>
      {speak_panel}
    </div>
  </div>
</body>
</html>
"""
    page_path.write_text(page_html, encoding="utf-8")
    return page_path
