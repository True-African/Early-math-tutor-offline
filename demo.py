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
from tutor.voice import build_child_greeting, build_silence_support, voice_button_html, voice_language_tag


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUTS_DIR = ROOT / "outputs"
DB_PATH = DATA_DIR / "local_store.sqlite"
SCHEMA_PATH = DATA_DIR / "seed" / "parent_report_schema.json"
KT_METRICS_PATH = OUTPUTS_DIR / "kt_metrics.json"
ASR_MODEL_DIR = ROOT / "models" / "asr"
ASR_QUANTIZED_MODEL_DIR = ROOT / "models" / "asr_quantized"
LORA_ADAPTER_DIR = ROOT / "models" / "lora_numeracy_adapter"
LORA_METADATA_PATH = LORA_ADAPTER_DIR / "adapter_metadata.json"
CURRICULUM = load_curriculum(DATA_DIR)

init_db(DB_PATH)

asr_service = OfflineASRService(
    str(ASR_MODEL_DIR) if ASR_MODEL_DIR.exists() else None,
    quantized_model_path=str(ASR_QUANTIZED_MODEL_DIR) if ASR_QUANTIZED_MODEL_DIR.exists() else None,
)
if LORA_METADATA_PATH.exists():
    metadata = json.loads(LORA_METADATA_PATH.read_text(encoding="utf-8"))
    lora_service = LoRALanguageHead(
        base_model=metadata.get("base_model"),
        adapter_path=metadata.get("adapter_path"),
    )
else:
    lora_service = LoRALanguageHead()


UI_TEXT = {
    "en": {
        "title": "Early Math Tutor Offline",
        "subtitle": "Adaptive numeracy practice with tap and microphone support.",
        "answer_label": "Tap an answer",
        "answer_highlight_label": "Tap one of the answer buttons below",
        "answer_highlight_info": "The tutor repeated the prompt after 10 seconds of silence and now points the child to these answer buttons.",
        "skill_label": "Current skill",
        "difficulty_label": "Difficulty",
        "prompt_hint": "Listen, count, and tap the matching answer button. You can also say the answer with the microphone.",
        "first_steps": "How to begin",
        "step_one": "Choose a language, enter a learner name, and start.",
        "step_two": "Listen, count, and tap the answer.",
        "step_three": "Open the caregiver report after an answer is saved.",
        "shared_tablet": "Shared tablet use",
        "shared_one": "Each child has a local learner profile on one device.",
        "shared_two": "Progress stays in local SQLite and survives reboot.",
        "shared_three": "Learners switch with a simple picker, not email or password.",
        "shared_four": "Any future sync should send only weekly summary statistics.",
        "welcome_title": "The opening experience is simple and voice-first",
        "welcome_line": "The learner hears the question clearly first.",
        "task_line": "A simple counting activity opens with four large answer buttons.",
        "support_line": "If the child stays silent, the tutor repeats slowly and highlights the taps.",
        "voice_note": "Current prompt",
        "silence_title": "The tutor repeats the prompt and guides a tap response",
        "language_label": "Tutor language",
        "learner_name_label": "New learner name",
        "learner_name_placeholder": "Type learner name",
        "learner_picker_label": "Existing learner",
        "start_button": "Start or switch learner",
        "typed_label": "Typed or spoken-word answer",
        "typed_placeholder": "e.g. five, cinq, esheshatu, 6",
        "submit_button": "Submit answer",
        "clear_button": "Clear answer",
        "mic_heading": "Microphone response",
        "mic_label": "Record child answer",
        "mic_button": "Transcribe microphone",
        "asr_placeholder": "ASR status will appear here.",
    },
    "kin": {
        "title": "Early Math Tutor Offline",
        "subtitle": "Porogaramu ifasha umwana kubara akoresheje gukanda no kuvuga.",
        "answer_label": "Kanda igisubizo",
        "answer_highlight_label": "Kanda kuri bumwe mu bisubizo hasi",
        "answer_highlight_info": "Mwarimu yasubiyemo ikibazo nyuma y'amasegonda 10 none yerekanye aho ukanda.",
        "skill_label": "Ubumenyi buriho",
        "difficulty_label": "Urwego",
        "prompt_hint": "Tega amatwi, bara, hanyuma ukande igisubizo. Ushobora no kugivuga ukoresheje mikoro.",
        "first_steps": "Uko watangira",
        "step_one": "Hitamo ururimi, andika izina ry'umwana, hanyuma utangire.",
        "step_two": "Tega amatwi, bara, hanyuma ukande igisubizo.",
        "step_three": "Nyuma yo kubika igisubizo, reba raporo y'umubyeyi.",
        "shared_tablet": "Gukoresha tabulete isangiwe",
        "shared_one": "Buri mwana agira umwirondoro we kuri icyo gikoresho.",
        "shared_two": "Aho ageze bibikwa muri SQLite kandi bikaguma nyuma yo kongera gufungura.",
        "shared_three": "Abana bahinduranya bakoresheje urutonde rw'amazina aho gukoresha email cyangwa ijambo banga.",
        "shared_four": "Nihagira koherezwa amakuru, hajye hajyayo imibare y'icyumweru gusa.",
        "welcome_title": "Gutangira bikorwa mu ijwi kandi byoroheje",
        "welcome_line": "Umwana abanza kumva ikibazo gisobanutse neza.",
        "task_line": "Hatangizwa igikorwa cyoroheje cyo kubara gifite ibisubizo bine binini.",
        "support_line": "Umwana acecetse, mwarimu asubiramo gahoro kandi akerekana aho ukanda.",
        "voice_note": "Ikibazo kiriho ubu",
        "silence_title": "Mwarimu asubiramo ikibazo kandi akayobora umwana gukanda",
        "language_label": "Ururimi rwa mwarimu",
        "learner_name_label": "Izina ry'umwana mushya",
        "learner_name_placeholder": "Andika izina ry'umwana",
        "learner_picker_label": "Umwana usanzwe ahari",
        "start_button": "Tangira cyangwa hindura umwana",
        "typed_label": "Igisubizo wanditse cyangwa wavuze",
        "typed_placeholder": "urugero: gatanu, five, cinq, 5",
        "submit_button": "Ohereza igisubizo",
        "clear_button": "Siba igisubizo",
        "mic_heading": "Igisubizo ukoresheje mikoro",
        "mic_label": "Fata amajwi y'igisubizo",
        "mic_button": "Hindura amajwi mo inyandiko",
        "asr_placeholder": "Ubutumwa bwa ASR buraza hano.",
    },
    "fr": {
        "title": "Early Math Tutor Offline",
        "subtitle": "Pratique adaptative de numératie avec réponse par toucher et microphone.",
        "answer_label": "Touchez une réponse",
        "answer_highlight_label": "Touchez une des réponses ci-dessous",
        "answer_highlight_info": "Le tuteur a répété la consigne après 10 secondes de silence et montre maintenant où toucher.",
        "skill_label": "Compétence en cours",
        "difficulty_label": "Difficulté",
        "prompt_hint": "Écoute, compte et touche la bonne réponse. Tu peux aussi répondre avec le microphone.",
        "first_steps": "Comment commencer",
        "step_one": "Choisissez une langue, entrez le nom de l'apprenant, puis démarrez.",
        "step_two": "Écoutez, comptez, puis touchez la réponse.",
        "step_three": "Ouvrez le rapport parent après l'enregistrement d'une réponse.",
        "shared_tablet": "Usage sur tablette partagée",
        "shared_one": "Chaque enfant a un profil local sur un seul appareil.",
        "shared_two": "Les progrès restent dans SQLite local et survivent au redémarrage.",
        "shared_three": "Les apprenants changent via une liste simple, sans email ni mot de passe.",
        "shared_four": "Toute synchronisation future devrait n'envoyer que des statistiques hebdomadaires.",
        "welcome_title": "L'ouverture est simple et guidée par la voix",
        "welcome_line": "L'apprenant entend d'abord la consigne clairement.",
        "task_line": "Une activité simple de comptage commence avec quatre grands boutons de réponse.",
        "support_line": "Si l'enfant reste silencieux, le tuteur répète lentement et met les boutons en avant.",
        "voice_note": "Consigne actuelle",
        "silence_title": "Le tuteur répète la consigne et guide le toucher",
        "language_label": "Langue du tuteur",
        "learner_name_label": "Nom du nouvel apprenant",
        "learner_name_placeholder": "Entrez le nom de l'apprenant",
        "learner_picker_label": "Apprenant existant",
        "start_button": "Démarrer ou changer d'apprenant",
        "typed_label": "Réponse écrite ou prononcée",
        "typed_placeholder": "ex. cinq, five, esheshatu, 6",
        "submit_button": "Valider la réponse",
        "clear_button": "Effacer la réponse",
        "mic_heading": "Réponse au microphone",
        "mic_label": "Enregistrer la réponse de l'enfant",
        "mic_button": "Transcrire le microphone",
        "asr_placeholder": "Le statut ASR apparaîtra ici.",
    },
}


def t(preferred_language: str, key: str) -> str:
    language = (preferred_language or "kin").lower()
    return UI_TEXT.get(language, UI_TEXT["en"]).get(key, UI_TEXT["en"].get(key, key))


TITLE_TEXT = {
    "en": "Early Math Tutor Offline",
    "kin": "Porogaramu yo Kwigisha Imibare y'Ibanze Idakenera Interineti",
    "fr": "Tuteur de Maths Elementaires Hors Ligne",
}

TAB_TEXT = {
    "en": ["Tutor Activity", "Caregiver Report", "Learner Progress", "Model & Offline Notes", "Download HTML Snapshot"],
    "kin": ["Igikorwa cya Mwarimu", "Raporo y'Umubyeyi", "Aho Umwana Ageze", "Amakuru ya Model na Offline", "Kubika HTML y'Ibisubizo"],
    "fr": ["Activite du Tuteur", "Rapport Parent", "Progres de l'Apprenant", "Notes Modele et Hors Ligne", "Telecharger l'Instantane HTML"],
}

MODEL_STATUS_TEXT = {
    "en": {
        "adaptation": "Child-speech augmentation is implemented in scripts/adapt_child_asr.py, and the ASR edge path now supports quantized CTranslate2 export for CPU devices.",
        "offline": "Tutor runtime uses only local curriculum, local storage, and optional local model folders.",
        "asr_ready": f"Quantized local ASR is available at {ASR_QUANTIZED_MODEL_DIR}.",
        "asr_missing": "No quantized local ASR model was found yet. Tap and typed answers still work.",
        "lora_ready": f"LoRA language head is loaded from {LORA_ADAPTER_DIR}.",
        "lora_missing": "LoRA language head is not configured yet.",
    },
    "kin": {
        "adaptation": "Guhuza amajwi y'abana byashyizwe muri scripts/adapt_child_asr.py, kandi inzira ya ASR yo ku gikoresho ishyigikira CTranslate2 quantized ku bikoresho bya CPU.",
        "offline": "Porogaramu ikoresha gusa integanyanyigisho zo mu gikoresho, ububiko bwo muri icyo gikoresho, n'amadosiye ya model yo mu gikoresho igihe ahari.",
        "asr_ready": f"ASR ya local ifite quantization iri muri {ASR_QUANTIZED_MODEL_DIR}.",
        "asr_missing": "Nta model ya ASR ya quantized local iraboneka. Gukanda no kwandika biracyakora.",
        "lora_ready": f"LoRA y'ururimi iri gukoresha dosiye zo muri {LORA_ADAPTER_DIR}.",
        "lora_missing": "LoRA y'ururimi ntirategurwa neza.",
    },
    "fr": {
        "adaptation": "L'adaptation de la voix des enfants est implementee dans scripts/adapt_child_asr.py, et le chemin ASR edge prend maintenant en charge une exportation CTranslate2 quantifiee pour les appareils CPU.",
        "offline": "Le tuteur fonctionne uniquement avec le curriculum local, le stockage local et les dossiers de modeles locaux optionnels.",
        "asr_ready": f"Le modele ASR local quantifie est disponible dans {ASR_QUANTIZED_MODEL_DIR}.",
        "asr_missing": "Aucun modele ASR local quantifie n'est encore disponible. Le toucher et la saisie restent disponibles.",
        "lora_ready": f"La tete de langage LoRA est chargee depuis {LORA_ADAPTER_DIR}.",
        "lora_missing": "La tete de langage LoRA n'est pas encore configuree.",
    },
}

EXTRA_TEXT = {
    "en": {
        "landing_audio": "Play start guide",
        "landing_audio_detail": "A short spoken guide starts automatically and explains how to begin.",
        "landing_guide": "Welcome. Choose a language, type a learner name, then press start. Listen, count, and tap the answer. After one answer, open the caregiver report.",
        "report_wait": "The weekly parent report will appear here after a learner starts answering items.",
        "progress_wait": "Learner progress will appear here after attempts are saved.",
        "snapshot_wait": "Start a learner session to generate the HTML dashboard.",
        "export_label": "Generated HTML dashboard",
    },
    "kin": {
        "landing_audio": "Tangira ubufasha bw'ijwi",
        "landing_audio_detail": "Iri jwi ritangira ubwaryo rikakwereka uko watangira.",
        "landing_guide": "Murakaza neza. Hitamo ururimi, andika izina ry'umwana, hanyuma ukande gutangira. Tega amatwi, bara, hanyuma ukande igisubizo. Nyuma y'igisubizo kimwe, reba raporo y'umubyeyi.",
        "report_wait": "Raporo y'umubyeyi izaza hano umwana namara gutangira gusubiza.",
        "progress_wait": "Aho umwana ageze hazaza hano ibisubizo nibimara kubikwa.",
        "snapshot_wait": "Tangira umwana kugira ngo ubyare HTML y'ibisubizo.",
        "export_label": "HTML y'ibisubizo yabazwe",
    },
    "fr": {
        "landing_audio": "Lire le guide de depart",
        "landing_audio_detail": "Un court guide audio se lance automatiquement pour expliquer comment commencer.",
        "landing_guide": "Bienvenue. Choisissez une langue, saisissez le nom de l'apprenant, puis appuyez sur demarrer. Ecoutez, comptez, puis touchez la reponse. Apres une reponse, ouvrez le rapport parent.",
        "report_wait": "Le rapport parent apparaitra ici apres les premieres reponses.",
        "progress_wait": "Les progres de l'apprenant apparaitront ici apres l'enregistrement des essais.",
        "snapshot_wait": "Demarrez une session apprenant pour generer le tableau HTML.",
        "export_label": "Tableau HTML genere",
    },
}


def title_text(preferred_language: str) -> str:
    return TITLE_TEXT.get((preferred_language or "kin").lower(), TITLE_TEXT["en"])


def extra_text(preferred_language: str, key: str) -> str:
    language = (preferred_language or "kin").lower()
    return EXTRA_TEXT.get(language, EXTRA_TEXT["en"]).get(key, EXTRA_TEXT["en"][key])


FEEDBACK_TEXT = {
    "en": {
        "session_ready_title": "Session ready",
        "session_ready_body": "The first question is shown above. After each answer, this box explains the previous question while the next one loads.",
        "silence_title": "Silence support after 10 seconds",
        "silence_body": "Ten seconds passed without an answer. The tutor repeated the prompt slowly and now points the child to the large answer buttons.",
        "action_needed": "Action needed",
        "start_first": "Start a learner session first.",
        "prev_answer_title": "Previous answer result",
        "prev_question": "Previous question",
        "your_answer": "Your answer",
        "detected_language": "Response language detected",
        "new_question": "A new question is now shown above.",
        "template_note": "Template feedback was used because the tiny local text model was not confident enough.",
        "no_answer": "no answer",
        "replay_slow": "Replay slow prompt",
        "replay_slow_detail": "This replay happens automatically after 10 seconds of silence and points the child back to the answer buttons.",
        "replay_welcome": "Replay welcome audio",
        "replay_welcome_detail": "The greeting auto-plays when a new learner starts in Hugging Face or the browser app.",
        "learner_none": "No learner yet",
        "tutor_feedback": "Tutor feedback",
        "first_activity_wait": "The first activity will appear here after you start a learner session.",
        "asr_prefix": "ASR status",
    },
    "kin": {
        "session_ready_title": "Uburyo bwiteguye",
        "session_ready_body": "Ikibazo cya mbere kiri hejuru. Nyuma ya buri gisubizo, aka gasanduku gasobanura igisubizo giheruka mu gihe ikibazo gikurikira kirimo kwitegura.",
        "silence_title": "Ubufasha nyuma y'amasegonda 10",
        "silence_body": "Amasegonda 10 ashize nta gisubizo. Mwarimu yasubiyemo ikibazo gahoro kandi none yerekanye aho ukanda ibisubizo binini.",
        "action_needed": "Harakenewe igikorwa",
        "start_first": "Banza utangize umwana.",
        "prev_answer_title": "Ibyavuyemo ku gisubizo giheruka",
        "prev_question": "Ikibazo giheruka",
        "your_answer": "Igisubizo cyawe",
        "detected_language": "Ururimi rwagaragaye",
        "new_question": "Ikibazo gishya kiri hejuru ubu.",
        "template_note": "Hifashishijwe ubutumwa bwateguwe kuko model nto yo ku gikoresho itari ifite icyizere gihagije.",
        "no_answer": "nta gisubizo",
        "replay_slow": "Subiramo ikibazo gahoro",
        "replay_slow_detail": "Iri subiramo ritangira nyuma y'amasegonda 10 kandi rikongera kwereka umwana aho akanda ibisubizo.",
        "replay_welcome": "Subiramo amajwi yo gutangira",
        "replay_welcome_detail": "Aya majwi atangira ubwayo iyo umwana mushya atangiye muri Hugging Face cyangwa muri porogaramu ya mushakisha.",
        "learner_none": "Nta mwana uratangira",
        "tutor_feedback": "Ubutumwa bwa mwarimu",
        "first_activity_wait": "Igikorwa cya mbere kizaza hano umaze gutangiza umwana.",
        "asr_prefix": "Uko ASR ihagaze",
    },
    "fr": {
        "session_ready_title": "Session prete",
        "session_ready_body": "La premiere question est affichee ci-dessus. Apres chaque reponse, cette zone explique la question precedente pendant que la suivante se charge.",
        "silence_title": "Aide apres 10 secondes",
        "silence_body": "Dix secondes se sont ecoulees sans reponse. Le tuteur a repete lentement la consigne et montre maintenant les grands boutons de reponse.",
        "action_needed": "Action requise",
        "start_first": "Commencez d'abord une session apprenant.",
        "prev_answer_title": "Resultat de la reponse precedente",
        "prev_question": "Question precedente",
        "your_answer": "Votre reponse",
        "detected_language": "Langue detectee",
        "new_question": "Une nouvelle question est maintenant affichee ci-dessus.",
        "template_note": "Un message modele a ete utilise parce que le petit modele local n'etait pas assez confiant.",
        "no_answer": "aucune reponse",
        "replay_slow": "Rejouer lentement la consigne",
        "replay_slow_detail": "Cette relance se joue automatiquement apres 10 secondes et montre a l'enfant ou toucher.",
        "replay_welcome": "Rejouer l'audio d'accueil",
        "replay_welcome_detail": "L'accueil se lance automatiquement lorsqu'un nouvel apprenant demarre dans Hugging Face ou dans l'application locale.",
        "learner_none": "Aucun apprenant pour le moment",
        "tutor_feedback": "Retour du tuteur",
        "first_activity_wait": "La premiere activite apparaitra ici apres le demarrage d'une session apprenant.",
        "asr_prefix": "Etat ASR",
    },
}

LANGUAGE_LABELS = {
    "en": {"unknown": "unknown", "mix": "mixed", "kin": "Kinyarwanda", "en": "English", "fr": "French"},
    "kin": {"unknown": "ntibizwi", "mix": "bivanze", "kin": "Ikinyarwanda", "en": "Icyongereza", "fr": "Igifaransa"},
    "fr": {"unknown": "inconnu", "mix": "melange", "kin": "Kinyarwanda", "en": "Anglais", "fr": "Francais"},
}


def ft(preferred_language: str, key: str) -> str:
    language = (preferred_language or "kin").lower()
    return FEEDBACK_TEXT.get(language, FEEDBACK_TEXT["en"]).get(key, FEEDBACK_TEXT["en"][key])


def detected_language_label(code: str, preferred_language: str) -> str:
    language = (preferred_language or "kin").lower()
    return LANGUAGE_LABELS.get(language, LANGUAGE_LABELS["en"]).get((code or "unknown").lower(), code or "unknown")


def localized_tabs_html(preferred_language: str) -> str:
    labels = json.dumps(TAB_TEXT.get((preferred_language or "kin").lower(), TAB_TEXT["en"]))
    js = html.escape(
        f"""
        (() => {{
          const labels = {labels};
          window.__emtTabRelabelVersion = (window.__emtTabRelabelVersion || 0) + 1;
          const version = window.__emtTabRelabelVersion;
          const apply = () => {{
            if (version !== window.__emtTabRelabelVersion) return;
            const tabs = Array.from(document.querySelectorAll('button[role="tab"]'));
            labels.forEach((label, index) => {{
              if (tabs[index]) {{
                tabs[index].textContent = label;
                tabs[index].setAttribute('aria-label', label);
              }}
            }});
          }};
          let attempt = 0;
          const tick = () => {{
            apply();
            attempt += 1;
            if (attempt < 8 && version === window.__emtTabRelabelVersion) {{
              setTimeout(tick, 120);
            }}
          }};
          requestAnimationFrame(tick);
        }})()
        """.strip(),
        quote=True,
    )
    return f"""
    <img alt="" src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==" style="display:none" onload="{js}">
    """


def landing_audio_html(preferred_language: str) -> str:
    return voice_button_html(
        extra_text(preferred_language, "landing_guide"),
        "rw-RW" if preferred_language == "kin" else ("fr-FR" if preferred_language == "fr" else "en-US"),
        extra_text(preferred_language, "landing_audio"),
        autoplay=True,
        detail=extra_text(preferred_language, "landing_audio_detail"),
    )


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


def choice_update(options: list[str], preferred_language: str = "kin", highlighted: bool = False):
    label = t(preferred_language, "answer_label")
    info = None
    if highlighted:
        label = t(preferred_language, "answer_highlight_label")
        info = t(preferred_language, "answer_highlight_info")
    return gr.update(choices=options, value=None, label=label, info=info)


def prompt_card(item: dict, preferred_language: str) -> str:
    reply_language = choose_reply_language(preferred_language, preferred_language)
    prompt = localized_stem(item, reply_language)
    skill = {
        "counting": {"en": "Counting", "kin": "Kubara", "fr": "Comptage"},
        "number_sense": {"en": "Number Sense", "kin": "Gusobanukirwa imibare", "fr": "Sens du nombre"},
        "addition": {"en": "Addition", "kin": "Guteranya", "fr": "Addition"},
        "subtraction": {"en": "Subtraction", "kin": "Gukuramo", "fr": "Soustraction"},
        "word_problem": {"en": "Word Problem", "kin": "Ibibazo by'amagambo", "fr": "Probleme verbal"},
    }.get(item["skill"], {}).get((preferred_language or "kin").lower(), item["skill"].replace("_", " ").title())
    difficulty = item.get("difficulty", 1)
    return f"""
    <div class="hero-card">
      <div class="eyebrow">{t(preferred_language, "skill_label")}: {skill} - {t(preferred_language, "difficulty_label")} {difficulty}</div>
      <div class="prompt-text">{prompt}</div>
      {render_visual_html(item)}
      <div class="hint-line">{t(preferred_language, "prompt_hint")}</div>
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


def scenario_card(preferred_language: str = "kin") -> str:
    return f"""
    <div class="panel-card opening-panel">
      <h3>{t(preferred_language, "first_steps")}</h3>
      {landing_audio_html(preferred_language)}
      <div class="journey-grid">
        <div class="journey-step">
          <div class="journey-icon">1</div>
          <div class="journey-copy">{t(preferred_language, "step_one")}</div>
        </div>
        <div class="journey-step">
          <div class="journey-icon">2</div>
          <div class="journey-copy">{t(preferred_language, "step_two")}</div>
        </div>
        <div class="journey-step">
          <div class="journey-icon">3</div>
          <div class="journey-copy">{t(preferred_language, "step_three")}</div>
        </div>
      </div>
    </div>
    """


def deployment_card(preferred_language: str = "kin") -> str:
    return f"""
    <div class="panel-card">
      <h3>{t(preferred_language, "shared_tablet")}</h3>
      <ul>
        <li>{t(preferred_language, "shared_one")}</li>
        <li>{t(preferred_language, "shared_two")}</li>
        <li>{t(preferred_language, "shared_three")}</li>
        <li>{t(preferred_language, "shared_four")}</li>
      </ul>
    </div>
    """


def build_model_status(preferred_language: str = "en") -> dict:
    asr_state = asr_status_snapshot(
        str(ASR_MODEL_DIR) if ASR_MODEL_DIR.exists() else None,
        quantized_model_path=str(ASR_QUANTIZED_MODEL_DIR) if ASR_QUANTIZED_MODEL_DIR.exists() else None,
        load_model=False,
    )
    lora_state = lora_service.status()
    language = (preferred_language or "en").lower()
    model_text = MODEL_STATUS_TEXT.get(language, MODEL_STATUS_TEXT["en"])
    return {
        "asr": model_text["asr_ready"] if asr_service.available() else model_text["asr_missing"],
        "asr_ready": asr_service.available(),
        "adaptation": model_text["adaptation"],
        "lora": model_text["lora_ready"] if lora_state["ready"] else model_text["lora_missing"],
        "lora_ready": lora_state["ready"],
        "offline": model_text["offline"],
    }


def refresh_system_dashboard(preferred_language: str = "kin") -> str:
    return system_dashboard_html(dashboard_snapshot(DB_PATH), KT_METRICS_PATH, build_model_status(preferred_language), preferred_language)


def learner_panels(learner_id: str, learner_name: str, preferred_language: str = "en") -> tuple[str, str]:
    report = build_weekly_report(DB_PATH, learner_id, SCHEMA_PATH, OUTPUTS_DIR)
    summary = learner_attempt_summary(DB_PATH, learner_id)
    attempts = recent_attempts(DB_PATH, learner_id, limit=12)
    return render_parent_report_html(report), learner_dashboard_html(learner_name, summary, attempts, preferred_language)


def export_views(learner_name: str, report_html: str, learner_html: str, system_html: str, preferred_language: str = "en") -> tuple[str, str]:
    bundle = export_results_bundle(OUTPUTS_DIR, learner_name, report_html, learner_html, system_html, preferred_language)
    return export_results_card(bundle, preferred_language), str(bundle["results_bundle"])


def choose_opening_item(curriculum: list[dict]) -> dict:
    goat_items = [
        item
        for item in curriculum
        if item.get("skill") == "counting"
        and ("goat" in item.get("stem_en", "").lower() or "goat" in item.get("visual", "").lower())
    ]
    candidates = goat_items or [item for item in curriculum if item.get("skill") == "counting"] or curriculum
    candidates.sort(key=lambda item: (int(item.get("difficulty", 1)), item.get("id", "")))
    return candidates[0]


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
    return f"""
    <div class="banner-card">
      <div class="banner-title">{title_text(preferred_language)}</div>
      <div class="banner-subtitle">{t(preferred_language, "subtitle")}</div>
    </div>
    """


def item_question_text(item: dict, preferred_language: str) -> str:
    reply_language = choose_reply_language(preferred_language, preferred_language)
    return localized_stem(item, reply_language)


def answer_label(raw_response: str, parsed: int | None, preferred_language: str = "kin") -> str:
    if parsed is not None:
        return str(parsed)
    if raw_response.strip():
        return raw_response.strip()
    return ft(preferred_language, "no_answer")


def opening_sequence_card(state: dict | None) -> str:
    if not state or not state.get("current_item"):
        return scenario_card("kin")

    preferred_language = state.get("preferred_language", "kin")
    raw_learner_name = state.get("learner_name", "Learner")
    learner_name = html.escape(raw_learner_name)
    item = state["current_item"]
    raw_question_local = localized_stem(item, preferred_language)
    raw_question_en = localized_stem(item, "en")
    raw_question_kin = localized_stem(item, "kin")
    question_local = html.escape(raw_question_local)
    question_en = html.escape(raw_question_en)
    question_kin = html.escape(raw_question_kin)
    local_icon = {"kin": "RW", "en": "EN", "fr": "FR"}.get(preferred_language, "RW")
    support_icon = "EN" if preferred_language == "kin" else "RW"
    support_question = question_en if preferred_language == "kin" else question_kin
    if preferred_language == "fr":
        support_question = question_kin or question_local
    learner_greeting = {"kin": "Muraho", "en": "Hello", "fr": "Bonjour"}.get(preferred_language, "Muraho")

    if state.get("first_run") and state.get("awaiting_first_answer"):
        if state.get("silence_prompt_shown"):
            silence_voice = voice_button_html(
                build_silence_support(raw_learner_name, raw_question_local, preferred_language),
                voice_language_tag(preferred_language),
                ft(preferred_language, "replay_slow"),
                autoplay=True,
                detail=ft(preferred_language, "replay_slow_detail"),
            )
            return f"""
            <div class="panel-card opening-panel">
              <h3>{t(preferred_language, "silence_title")}</h3>
              <div class="journey-grid compact-grid">
                <div class="journey-step">
                  <div class="journey-icon">{local_icon}</div>
                  <div class="journey-copy">{question_local}</div>
                </div>
                <div class="journey-step">
                  <div class="journey-icon">{support_icon}</div>
                  <div class="journey-copy">{support_question}</div>
                </div>
                <div class="journey-step">
                  <div class="journey-icon">TAP</div>
                  <div class="journey-copy">{t(preferred_language, "step_two")}</div>
                </div>
              </div>
              {silence_voice}
            </div>
            """

        welcome_voice = voice_button_html(
            build_child_greeting(raw_learner_name, raw_question_local, preferred_language),
            voice_language_tag(preferred_language),
            ft(preferred_language, "replay_welcome"),
            autoplay=True,
            detail=ft(preferred_language, "replay_welcome_detail"),
        )
        return f"""
        <div class="panel-card opening-panel">
          <h3>{t(preferred_language, "welcome_title")}</h3>
          <div class="journey-grid compact-grid">
            <div class="journey-step">
              <div class="journey-icon">{local_icon}</div>
              <div class="journey-copy">{learner_greeting} {learner_name}. {t(preferred_language, "welcome_line")}</div>
            </div>
            <div class="journey-step">
              <div class="journey-icon">123</div>
              <div class="journey-copy">{t(preferred_language, "task_line")}</div>
            </div>
            <div class="journey-step">
              <div class="journey-icon">10s</div>
              <div class="journey-copy">{t(preferred_language, "support_line")}</div>
            </div>
          </div>
          <div class="voice-inline-note">{t(preferred_language, "voice_note")}: {question_local}</div>
          {welcome_voice}
        </div>
        """

    return scenario_card(preferred_language)


def refresh_language_ui(preferred_language: str, state: dict):
    preferred_language = (preferred_language or "kin").lower()
    state = dict(state or {})
    if state.get("current_item"):
        state["preferred_language"] = preferred_language
        opening_html = opening_sequence_card(state)
        prompt_html = prompt_card(state["current_item"], preferred_language)
        choice_html = choice_update(
            state.get("current_options") or [],
            preferred_language,
            highlighted=bool(state.get("silence_prompt_shown")),
        )
        banner_html = session_banner(state.get("learner_name", "Learner"), preferred_language)
        report_html, learner_html = learner_panels(state["learner_id"], state["learner_name"], preferred_language)
        system_html = system_dashboard_html(dashboard_snapshot(DB_PATH), KT_METRICS_PATH, build_model_status(preferred_language), preferred_language)
        export_html, _ = export_views(state["learner_name"], report_html, learner_html, system_html, preferred_language)
    else:
        opening_html = scenario_card(preferred_language)
        prompt_html = "<div></div>"
        choice_html = gr.update(label=t(preferred_language, "answer_label"), info=None)
        banner_html = session_banner(ft(preferred_language, "learner_none"), preferred_language)
        report_html = f"<p style='color:#60707d'>{html.escape(extra_text(preferred_language, 'report_wait'))}</p>"
        learner_html = f"<p style='color:#60707d'>{html.escape(extra_text(preferred_language, 'progress_wait'))}</p>"
        system_html = system_dashboard_html(dashboard_snapshot(DB_PATH), KT_METRICS_PATH, build_model_status(preferred_language), preferred_language)
        export_html = f"<p style='color:#60707d'>{html.escape(extra_text(preferred_language, 'snapshot_wait'))}</p>"

    return (
        banner_html,
        localized_tabs_html(preferred_language),
        opening_html,
        prompt_html,
        choice_html,
        report_html,
        learner_html,
        system_html,
        export_html,
        gr.update(label=t(preferred_language, "typed_label"), placeholder=t(preferred_language, "typed_placeholder")),
        gr.update(label=t(preferred_language, "learner_name_label"), placeholder=t(preferred_language, "learner_name_placeholder")),
        gr.update(label=t(preferred_language, "learner_picker_label")),
        gr.update(label=t(preferred_language, "language_label")),
        gr.update(value=t(preferred_language, "start_button")),
        gr.update(value=t(preferred_language, "submit_button")),
        gr.update(value=t(preferred_language, "clear_button")),
        f"### {t(preferred_language, 'mic_heading')}",
        gr.update(label=t(preferred_language, "mic_label")),
        gr.update(value=t(preferred_language, "mic_button")),
        t(preferred_language, "asr_placeholder"),
        gr.update(label=extra_text(preferred_language, "export_label")),
        deployment_card(preferred_language),
        state,
    )


def start_session(learner_name: str, learner_choice: str, preferred_language: str):
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
    summary = learner_attempt_summary(DB_PATH, learner_id)
    is_first_run = summary["total_attempts"] == 0
    item = choose_opening_item(CURRICULUM) if is_first_run else choose_next_item(CURRICULUM, mastery, recent_ids)
    options = build_options(int(item["answer_int"]), item["id"])
    state = make_state(learner_id, learner_name, preferred_language, mastery, item, recent_ids + [item["id"]])
    state["first_run"] = is_first_run
    state["awaiting_first_answer"] = is_first_run
    state["silence_prompt_shown"] = False
    state["first_run_complete"] = False
    state["current_options"] = options

    report_html, learner_html = learner_panels(learner_id, learner_name, preferred_language)
    system_html = system_dashboard_html(dashboard_snapshot(DB_PATH), KT_METRICS_PATH, build_model_status(preferred_language), preferred_language)
    export_html, export_file = export_views(learner_name, report_html, learner_html, system_html, preferred_language)
    asr_status = asr_service.status()["message"]

    return (
        session_banner(learner_name, preferred_language),
        opening_sequence_card(state),
        prompt_card(item, preferred_language),
        choice_update(options, preferred_language),
        "",
        feedback_card(
            ft(preferred_language, "session_ready_body"),
            positive=True,
            title=ft(preferred_language, "session_ready_title"),
        ),
        report_html,
        learner_html,
        system_html,
        export_html,
        export_file,
        f"{ft(preferred_language, 'asr_prefix')}: {asr_status}",
        gr.update(value=10, active=is_first_run),
        state,
        gr.update(choices=learner_choices(), value=f"{learner_name} [{learner_id}]"),
    )


def handle_silence_timeout(state: dict):
    if not state or not state.get("awaiting_first_answer") or state.get("silence_prompt_shown") or not state.get("current_item"):
        return gr.skip(), gr.skip(), gr.skip(), gr.update(active=False), state
    state["silence_prompt_shown"] = True
    options = state.get("current_options") or build_options(int(state["current_item"]["answer_int"]), state["current_item"]["id"])
    feedback_text = ft(state.get("preferred_language", "kin"), "silence_body")
    return (
        opening_sequence_card(state),
        feedback_card(feedback_text, positive=True, title=ft(state.get("preferred_language", "kin"), "silence_title")),
        choice_update(options, state.get("preferred_language", "kin"), highlighted=True),
        gr.update(active=False),
        state,
    )


def transcribe_microphone(audio_blob, state: dict):
    if not state or not state.get("current_item"):
        return "", ft("kin", "start_first")
    result = asr_service.transcribe(audio_blob, preferred_language=state.get("preferred_language", "kin"))
    if result["text"]:
        return result["text"], result["message"]
    return "", result["message"]


def submit_answer(choice: str, typed_answer: str, state: dict):
    if not state or not state.get("current_item"):
        return (
            session_banner(ft("kin", "learner_none"), "kin"),
            opening_sequence_card(None),
            "<div></div>",
            gr.update(choices=[], value=None),
            "",
            feedback_card(ft("kin", "start_first"), positive=False, title=ft("kin", "action_needed")),
            f"<p style='color:#60707d'>{html.escape(extra_text('kin', 'report_wait'))}</p>",
            f"<p style='color:#60707d'>{html.escape(extra_text('kin', 'progress_wait'))}</p>",
            system_dashboard_html(dashboard_snapshot(DB_PATH), KT_METRICS_PATH, build_model_status("kin"), "kin"),
            f"<p style='color:#60707d'>{html.escape(extra_text('kin', 'snapshot_wait'))}</p>",
            None,
            t("kin", "asr_placeholder"),
            gr.update(value=10, active=False),
            state,
            gr.update(choices=learner_choices()),
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
        f"{ft(state['preferred_language'], 'prev_question')}: {question_text}. "
        f"{ft(state['preferred_language'], 'your_answer')}: {answer_label(raw_response or '', parsed, state['preferred_language'])}. "
        f"{feedback_payload['text']} "
        f"{ft(state['preferred_language'], 'detected_language')}: {detected_language_label(detected or 'unknown', state['preferred_language'])}. "
        f"{ft(state['preferred_language'], 'new_question')}"
    )
    if feedback_payload.get("error"):
        feedback_text += f" {ft(state['preferred_language'], 'template_note')}"

    recent_ids = (state.get("recent_ids") or [])[-5:] + [item["id"]]
    next_item = choose_next_item(CURRICULUM, mastery, recent_ids)
    options = build_options(int(next_item["answer_int"]), next_item["id"])

    state["mastery"] = mastery
    state["current_item"] = next_item
    state["recent_ids"] = recent_ids + [next_item["id"]]
    state["current_options"] = options
    state["awaiting_first_answer"] = False
    state["first_run_complete"] = bool(state.get("first_run"))

    report_html, learner_html = learner_panels(state["learner_id"], state["learner_name"], state["preferred_language"])
    system_html = system_dashboard_html(dashboard_snapshot(DB_PATH), KT_METRICS_PATH, build_model_status(state["preferred_language"]), state["preferred_language"])
    export_html, export_file = export_views(state["learner_name"], report_html, learner_html, system_html, state["preferred_language"])
    asr_status = asr_service.status()["message"]

    return (
        session_banner(state["learner_name"], state["preferred_language"]),
        opening_sequence_card(state),
        prompt_card(next_item, state["preferred_language"]),
        choice_update(options, state["preferred_language"]),
        "",
        feedback_card(feedback_text, positive=correct, title=ft(state["preferred_language"], "prev_answer_title")),
        report_html,
        learner_html,
        system_html,
        export_html,
        export_file,
        f"{ft(state['preferred_language'], 'asr_prefix')}: {asr_status}",
        gr.update(value=10, active=False),
        state,
        gr.update(choices=learner_choices(), value=f"{state['learner_name']} [{state['learner_id']}]"),
    )


CUSTOM_CSS = """
body, .gradio-container {background:#f4f7f8 !important; font-family:Arial,Helvetica,sans-serif}
.app-shell {max-width:1400px;margin:0 auto}
.hero-card {background:#ffffff;border:1px solid #dce5ea;border-radius:18px;padding:18px}
.learning-stage {background:#ffffff;border:1px solid #f1dfc3;border-radius:18px;padding:18px;box-shadow:0 8px 24px rgba(15,61,69,0.08)}
.eyebrow {font-size:12px;color:#60707d;margin-bottom:8px;text-transform:uppercase;letter-spacing:.04em}
.prompt-text {font-size:32px;font-weight:700;line-height:1.3;margin-bottom:14px;color:#17212b}
.hint-line {margin-top:10px;color:#60707d;font-size:13px}
.banner-card {display:block;background:linear-gradient(135deg,#0f3d45 0%,#155660 100%);color:#f7fbfc;padding:18px 20px;border-radius:18px;margin-bottom:10px}
.banner-title {font-size:30px;font-weight:800;line-height:1.1}
.banner-subtitle {margin-top:6px;color:#d6e7ea;font-size:15px}
.lang-panel {background:#ffffff;border:1px solid #dce5ea;border-radius:14px;padding:8px 10px}
.panel-card {background:#ffffff;border:1px solid #dce5ea;border-radius:14px;padding:16px}
.opening-panel {margin-bottom:14px;background:#fff8ec;border-color:#f7c37a}
.journey-grid {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.compact-grid {grid-template-columns:repeat(3,minmax(0,1fr));margin-bottom:14px}
.journey-step {background:#ffffff;border:1px solid #f1dfc3;border-radius:18px;padding:14px}
.journey-icon {width:44px;height:44px;border-radius:14px;background:#ef6c2f;color:#ffffff;font-weight:800;display:grid;place-items:center;margin-bottom:10px}
.journey-title {font-size:18px;font-weight:700;color:#17212b;margin-bottom:6px}
.journey-copy {color:#60707d;line-height:1.45}
.voice-box {background:#ffffff;border:1px solid #f1dfc3;border-radius:18px;padding:14px}
.voice-btn {border:0;border-radius:999px;background:#ef6c2f;color:#ffffff;padding:12px 16px;font-size:16px;font-weight:800;cursor:pointer}
.voice-detail {margin-top:8px;color:#60707d;line-height:1.45}
.voice-inline-note {margin-bottom:12px;color:#4f5f6b}
#answer-buttons label {min-height:72px !important;border-radius:18px !important;border:2px solid #dce5ea !important;background:#fff !important;font-size:24px !important;font-weight:800 !important;display:flex !important;align-items:center !important;justify-content:center !important}
#answer-buttons label:has(input:checked) {border-color:#ef6c2f !important;background:#fff4ea !important}
@media (max-width: 900px) {.journey-grid,.compact-grid {grid-template-columns:1fr}}
"""


with gr.Blocks(title="Early Math Tutor Offline") as demo:
    app_state = gr.State({})
    tab_labels_html = gr.HTML(localized_tabs_html("kin"))

    with gr.Row():
        with gr.Column(scale=10):
            status_html = gr.HTML(session_banner(ft("kin", "learner_none"), "kin"))
        with gr.Column(scale=3, elem_classes=["lang-panel"]):
            preferred_language = gr.Dropdown(
                label=t("kin", "language_label"),
                choices=[("Kinyarwanda", "kin"), ("English", "en"), ("Français", "fr")],
                value="kin",
            )

    with gr.Tabs():
        with gr.Tab("Tutor Activity"):
            with gr.Row():
                with gr.Column(scale=4):
                    opening_html = gr.HTML(opening_sequence_card(None))
                    learner_name = gr.Textbox(label=t("kin", "learner_name_label"), placeholder=t("kin", "learner_name_placeholder"))
                    learner_picker = gr.Dropdown(label=t("kin", "learner_picker_label"), choices=learner_choices(), allow_custom_value=False)
                    start_btn = gr.Button(t("kin", "start_button"), variant="primary")
                    mic_heading = gr.Markdown(f"### {t('kin', 'mic_heading')}")
                    mic = gr.Audio(label=t("kin", "mic_label"), sources=["microphone"], type="numpy")
                    use_mic_btn = gr.Button(t("kin", "mic_button"))
                    asr_status = gr.Markdown(t("kin", "asr_placeholder"))
                    deployment_html = gr.HTML(deployment_card("kin"))
                with gr.Column(scale=8):
                    with gr.Group(elem_classes=["learning-stage"]):
                        prompt_html = gr.HTML("<div></div>")
                        choice = gr.Radio(label=t("kin", "answer_label"), choices=[], elem_id="answer-buttons")
                        typed_answer = gr.Textbox(label=t("kin", "typed_label"), placeholder=t("kin", "typed_placeholder"))
                        with gr.Row():
                            submit_btn = gr.Button(t("kin", "submit_button"), variant="primary")
                            clear_btn = gr.Button(t("kin", "clear_button"))
                        feedback_html = gr.HTML(
                            feedback_card(
                                ft("kin", "first_activity_wait"),
                                positive=True,
                                title=ft("kin", "tutor_feedback"),
                            )
                        )

        with gr.Tab("Caregiver Report"):
            report_html = gr.HTML(
                f"<p style='color:#60707d'>{html.escape(extra_text('kin', 'report_wait'))}</p>"
            )

        with gr.Tab("Learner Progress"):
            learner_html = gr.HTML(
                f"<p style='color:#60707d'>{html.escape(extra_text('kin', 'progress_wait'))}</p>"
            )

        with gr.Tab("Model & Offline Notes"):
            system_html = gr.HTML(refresh_system_dashboard())

        with gr.Tab("Download HTML Snapshot"):
            html_exports = gr.HTML(
                f"<p style='color:#60707d'>{html.escape(extra_text('kin', 'snapshot_wait'))}</p>"
            )
            export_file = gr.File(label=extra_text('kin', 'export_label'), file_count="single")

    silence_timer = gr.Timer(value=10, active=False)

    start_btn.click(
        start_session,
        inputs=[learner_name, learner_picker, preferred_language],
        outputs=[
            status_html,
            opening_html,
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
            silence_timer,
            app_state,
            learner_picker,
        ],
    )
    preferred_language.change(
        refresh_language_ui,
        inputs=[preferred_language, app_state],
        outputs=[
            status_html,
            tab_labels_html,
            opening_html,
            prompt_html,
            choice,
            report_html,
            learner_html,
            system_html,
            html_exports,
            typed_answer,
            learner_name,
            learner_picker,
            preferred_language,
            start_btn,
            submit_btn,
            clear_btn,
            mic_heading,
            mic,
            use_mic_btn,
            asr_status,
            export_file,
            deployment_html,
            app_state,
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
            opening_html,
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
            silence_timer,
            app_state,
            learner_picker,
        ],
    )
    clear_btn.click(lambda: "", outputs=[typed_answer])
    silence_timer.tick(
        handle_silence_timeout,
        inputs=[app_state],
        outputs=[opening_html, feedback_html, choice, silence_timer, app_state],
    )


if __name__ == "__main__":
    demo.launch(css=CUSTOM_CSS)
