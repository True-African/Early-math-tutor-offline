from __future__ import annotations

import json
from pathlib import Path

from tutor.voice import skill_label


TEXT = {
    "en": {
        "no_attempts": "No attempts yet.",
        "no_language": "No language data yet.",
        "no_recent": "No recent attempts yet.",
        "skill": "Skill",
        "progress": "Progress",
        "accuracy": "Accuracy",
        "attempts": "Attempts",
        "answer": "Answer",
        "language": "Language",
        "learner": "Learner",
        "unknown": "unknown",
        "mix": "mixed",
        "refresh": "Refreshes after each answer",
        "autorefresh": "HTML auto-refresh: 4 seconds",
        "howto": "Dashboard",
        "howto_meta": "A compact local dashboard with collapsible sections for parent, learner, and system views.",
        "parent_report": "Parent report",
        "parent_meta": "Weekly caregiver summary.",
        "learner_dashboard": "Learner dashboard",
        "learner_meta": "Progress, language mix, and recent answers.",
        "system_dashboard": "System dashboard",
        "system_meta": "Tutor metrics, readiness, and recent activity.",
        "results_title": "Tutor Results Dashboard",
        "results_subtitle": "One standalone page with collapsible learner and system cards.",
        "saved": "HTML dashboard saved",
        "saved_meta": "Open this standalone dashboard outside Gradio.",
        "correct": "Correct",
        "skill_progress": "Skill progress",
        "language_mix": "Language mix",
        "recent_answers": "Latest answers",
        "learners": "Learners",
        "skill_accuracy": "Skill accuracy",
        "recent_activity": "Recent activity",
        "model_readiness": "Model readiness",
        "child_adapt": "Child-speech adaptation",
        "lora": "LoRA language head",
        "offline": "Offline runtime",
        "kt_missing": "KT evaluation has not been run yet.",
        "language_overview": "Language overview",
        "status_ready": "ready",
        "status_not_ready": "not ready",
        "overview": "Overview",
        "details": "Details",
        "collapse_hint": "Tap to expand or collapse",
        "health_strip": "Recent status strip",
        "recent_table": "Recent table",
    },
    "kin": {
        "no_attempts": "Nta bisubizo birabikwa.",
        "no_language": "Nta makuru y'ururimi araza.",
        "no_recent": "Nta bisubizo bya vuba bihari.",
        "skill": "Ubumenyi",
        "progress": "Aho ageze",
        "accuracy": "Ukuri",
        "attempts": "Inshuro",
        "answer": "Igisubizo",
        "language": "Ururimi",
        "learner": "Umwana",
        "unknown": "ntibizwi",
        "mix": "bivanze",
        "refresh": "Yisubiraho nyuma ya buri gisubizo",
        "autorefresh": "HTML yisubiraho buri masegonda 4",
        "howto": "Imbonerahamwe",
        "howto_meta": "Imbonerahamwe ngufi yo ku gikoresho ifite ibice bifunguka kandi bifunga ku mubyeyi, umwana, na sisitemu.",
        "parent_report": "Raporo y'umubyeyi",
        "parent_meta": "Incamake y'icyumweru y'umurera.",
        "learner_dashboard": "Aho umwana ageze",
        "learner_meta": "Iterambere, indimi zakoreshejwe, n'ibisubizo bya vuba.",
        "system_dashboard": "Aho sisitemu igeze",
        "system_meta": "Imibare ya porogaramu, uko biteguye, n'ibikorwa bya vuba.",
        "results_title": "Imbonerahamwe y'ibisubizo",
        "results_subtitle": "Paji imwe ifite amakarita y'umwana na sisitemu afunguka kandi agafunga.",
        "saved": "HTML yabitswe",
        "saved_meta": "Fungura iyi HTML hanze ya Gradio.",
        "correct": "Byo neza",
        "skill_progress": "Iterambere ku bumenyi",
        "language_mix": "Indimi zakoreshejwe",
        "recent_answers": "Ibisubizo bya vuba",
        "learners": "Abana",
        "skill_accuracy": "Ukuri ku bumenyi",
        "recent_activity": "Ibikorwa bya vuba",
        "model_readiness": "Uko model zihagaze",
        "child_adapt": "Guhuza amajwi y'abana",
        "lora": "LoRA y'ururimi",
        "offline": "Gukorera offline",
        "kt_missing": "Isuzuma rya KT ntirirakorwa.",
        "language_overview": "Incamake y'indimi",
        "status_ready": "biteguye",
        "status_not_ready": "ntibiriteguye",
        "overview": "Ishusho rusange",
        "details": "Ibisobanuro",
        "collapse_hint": "Kanda ufungure cyangwa ufunge",
        "health_strip": "Umurongo w'uko byifashe vuba",
        "recent_table": "Imbonerahamwe ya vuba",
    },
    "fr": {
        "no_attempts": "Aucune reponse pour le moment.",
        "no_language": "Aucune donnee de langue pour le moment.",
        "no_recent": "Aucune reponse recente.",
        "skill": "Competence",
        "progress": "Progression",
        "accuracy": "Precision",
        "attempts": "Essais",
        "answer": "Reponse",
        "language": "Langue",
        "learner": "Apprenant",
        "unknown": "inconnu",
        "mix": "melange",
        "refresh": "Se met a jour apres chaque reponse",
        "autorefresh": "Rafraichissement HTML : 4 secondes",
        "howto": "Tableau",
        "howto_meta": "Un tableau local compact avec sections repliables pour le parent, l'apprenant et le systeme.",
        "parent_report": "Rapport parent",
        "parent_meta": "Resume hebdomadaire pour le parent.",
        "learner_dashboard": "Tableau de l'apprenant",
        "learner_meta": "Progression, langues utilisees et reponses recentes.",
        "system_dashboard": "Tableau systeme",
        "system_meta": "Mesures du tuteur, etat de preparation et activite recente.",
        "results_title": "Tableau des resultats du tuteur",
        "results_subtitle": "Une seule page avec cartes repliables pour l'apprenant et le systeme.",
        "saved": "Tableau HTML enregistre",
        "saved_meta": "Ouvrez ce tableau HTML hors de Gradio.",
        "correct": "Correct",
        "skill_progress": "Progression par competence",
        "language_mix": "Repartition des langues",
        "recent_answers": "Dernieres reponses",
        "learners": "Apprenants",
        "skill_accuracy": "Precision par competence",
        "recent_activity": "Activite recente",
        "model_readiness": "Etat des modeles",
        "child_adapt": "Adaptation voix enfantine",
        "lora": "Tete de langage LoRA",
        "offline": "Fonctionnement hors ligne",
        "kt_missing": "L'evaluation KT n'a pas encore ete executee.",
        "language_overview": "Vue des langues",
        "status_ready": "pret",
        "status_not_ready": "non pret",
        "overview": "Vue d'ensemble",
        "details": "Details",
        "collapse_hint": "Touchez pour ouvrir ou fermer",
        "health_strip": "Bande de statut recent",
        "recent_table": "Table recente",
    },
}


def tr(language: str, key: str) -> str:
    language = (language or "en").lower()
    return TEXT.get(language, TEXT["en"]).get(key, TEXT["en"].get(key, key))


def _kt_summary(metrics: dict, language: str) -> str:
    if not metrics:
        return tr(language, "kt_missing")
    learners = metrics.get("learners", 0)
    events = metrics.get("events", 0)
    bkt_auc = metrics.get("bkt_auc", "TODO")
    elo_auc = metrics.get("elo_auc", "TODO")
    templates = {
        "en": f"Held-out replay: {learners} learners, {events} answer events. BKT AUC {bkt_auc}; Elo AUC {elo_auc}.",
        "kin": f"Replay yabigenewe: abana {learners}, ibisubizo {events}. BKT AUC {bkt_auc}; Elo AUC {elo_auc}.",
        "fr": f"Rejeu separe : {learners} apprenants, {events} reponses. BKT AUC {bkt_auc} ; Elo AUC {elo_auc}.",
    }
    return templates.get((language or "en").lower(), templates["en"])


def _skill_name(skill: str, language: str) -> str:
    return skill_label(skill, language)


def _language_name(code: str, language: str) -> str:
    labels = {
        "en": {"kin": "Kinyarwanda", "en": "English", "fr": "French"},
        "kin": {"kin": "Ikinyarwanda", "en": "Icyongereza", "fr": "Igifaransa"},
        "fr": {"kin": "Kinyarwanda", "en": "Anglais", "fr": "Francais"},
    }
    code = (code or "unknown").lower()
    base = labels.get((language or "en").lower(), labels["en"])
    if code in {"unknown", "mix"}:
        return tr(language, code)
    return base.get(code, code)


def _theme_css() -> str:
    return """
    <style>
      .nd-shell{font-family:Arial,Helvetica,sans-serif;background:#fffdf8;color:#17212b;border:1px solid #dce5ea;border-radius:18px;padding:16px}
      .nd-header{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:14px}
      .nd-title{font-size:24px;font-weight:800;margin:0}
      .nd-meta{color:#60707d;font-size:13px}
      .nd-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
      .nd-tile{background:#ffffff;border:1px solid #dce5ea;border-radius:14px;padding:12px}
      .nd-label{color:#60707d;font-size:12px;text-transform:uppercase;letter-spacing:.05em}
      .nd-value{font-size:28px;font-weight:800;margin-top:6px}
      .nd-sub{color:#60707d;font-size:12px;margin-top:6px}
      .nd-strip{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
      .nd-dot{width:12px;height:12px;border-radius:999px;display:inline-block;background:#2a9d8f}
      .nd-dot.bad{background:#e85d75}
      .nd-dot.mid{background:#f4a261}
      .nd-section{margin-top:14px;background:#ffffff;border:1px solid #dce5ea;border-radius:16px;overflow:hidden}
      .nd-section>summary{list-style:none;cursor:pointer;padding:14px 16px;font-weight:700;background:#f7fafb;border-bottom:1px solid #dce5ea}
      .nd-section>summary::-webkit-details-marker{display:none}
      .nd-section-body{padding:14px 16px}
      .nd-two{display:grid;grid-template-columns:1.4fr .9fr;gap:14px}
      .nd-table{width:100%;border-collapse:collapse}
      .nd-table th,.nd-table td{padding:10px 8px;border-bottom:1px solid #dce5ea;text-align:left}
      .nd-table th{color:#60707d;font-size:12px;text-transform:uppercase}
      .nd-progress{height:10px;background:#eef3f6;border-radius:999px;overflow:hidden;border:1px solid #dce5ea}
      .nd-fill{height:100%;background:linear-gradient(90deg,#00c853,#2dd4bf)}
      .nd-fill.mid{background:linear-gradient(90deg,#ffb703,#fb8500)}
      .nd-fill.low{background:linear-gradient(90deg,#ef476f,#ff6b6b)}
      .nd-legend{display:flex;flex-direction:column;gap:8px}
      .nd-legend-row{display:flex;align-items:center;gap:8px;color:#17212b}
      .nd-swatch{width:12px;height:12px;border-radius:999px;display:inline-block}
      .nd-note{color:#60707d;font-size:13px;line-height:1.45}
      .nd-pill{display:inline-block;padding:6px 10px;border-radius:999px;background:#fff8ec;border:1px solid #f1dfc3;color:#17212b;margin-right:8px}
      @media (max-width: 900px){.nd-grid,.nd-two{grid-template-columns:1fr}}
    </style>
    """


def _metric_tile(label: str, value: str, sub: str = "") -> str:
    return (
        "<div class='nd-tile'>"
        f"<div class='nd-label'>{label}</div>"
        f"<div class='nd-value'>{value}</div>"
        f"<div class='nd-sub'>{sub}</div>"
        "</div>"
    )


def _level_class(percent: int) -> str:
    if percent >= 75:
        return ""
    if percent >= 45:
        return " mid"
    return " low"


def _health_strip(rows: list[dict]) -> str:
    if not rows:
        return ""
    dots = []
    for row in rows[:32]:
        klass = "" if row.get("correct") else " bad"
        dots.append(f"<span class='nd-dot{klass}'></span>")
    return f"<div class='nd-strip'>{''.join(dots)}</div>"


def _skill_table(rows: list[dict], language: str) -> str:
    if not rows:
        return f"<p class='nd-note'>{tr(language, 'no_attempts')}</p>"
    out = []
    for row in rows:
        percent = int(row["accuracy"] * 100)
        out.append(
            "<tr>"
            f"<td>{_skill_name(row['skill'], language)}</td>"
            f"<td><div class='nd-progress'><div class='nd-fill{_level_class(percent)}' style='width:{percent}%'></div></div></td>"
            f"<td>{percent}%</td>"
            f"<td>{row['attempts']}</td>"
            "</tr>"
        )
    return (
        "<table class='nd-table'>"
        f"<thead><tr><th>{tr(language, 'skill')}</th><th>{tr(language, 'progress')}</th><th>{tr(language, 'accuracy')}</th><th>{tr(language, 'attempts')}</th></tr></thead>"
        f"<tbody>{''.join(out)}</tbody></table>"
    )


def _language_panel(rows: list[dict], language: str) -> str:
    if not rows:
        return f"<p class='nd-note'>{tr(language, 'no_language')}</p>"
    total = max(sum(int(row.get("count", 0)) for row in rows), 1)
    colors = ["#00c853", "#2dd4bf", "#ffb703", "#ef476f", "#8d99ae"]
    start = 0
    gradient_parts = []
    legend = []
    for index, row in enumerate(rows):
        count = int(row.get("count", 0))
        pct = round(count / total * 100)
        end = start + pct
        color = colors[index % len(colors)]
        gradient_parts.append(f"{color} {start}% {end}%")
        legend.append(
            "<div class='nd-legend-row'>"
            f"<span class='nd-swatch' style='background:{color}'></span>"
            f"<span>{_language_name(row.get('language', 'unknown'), language)}: {count}</span>"
            "</div>"
        )
        start = end
    return (
        "<div class='nd-two' style='grid-template-columns:160px 1fr;align-items:center'>"
        f"<div style='width:160px;height:160px;border-radius:999px;background:conic-gradient({', '.join(gradient_parts)});border:1px solid #243241'></div>"
        f"<div class='nd-legend'>{''.join(legend)}</div>"
        "</div>"
    )


def _recent_table(rows: list[dict], language: str) -> str:
    if not rows:
        return f"<p class='nd-note'>{tr(language, 'no_recent')}</p>"
    out = []
    for row in rows[:10]:
        answer = row.get("response_value") if row.get("response_value") is not None else row.get("response_text", "")
        out.append(
            "<tr>"
            f"<td>{_skill_name(row['skill'], language)}</td>"
            f"<td>{answer}</td>"
            f"<td>{_language_name(row.get('language_detected') or 'unknown', language)}</td>"
            f"<td>{row['created_at']}</td>"
            "</tr>"
        )
    return (
        "<table class='nd-table'>"
        f"<thead><tr><th>{tr(language, 'skill')}</th><th>{tr(language, 'answer')}</th><th>{tr(language, 'language')}</th><th>{tr(language, 'details')}</th></tr></thead>"
        f"<tbody>{''.join(out)}</tbody></table>"
    )


def _section(title: str, body: str, language: str, *, open_: bool = True, meta: str = "") -> str:
    open_attr = " open" if open_ else ""
    meta_html = f"<div class='nd-note' style='margin-bottom:12px'>{meta}</div>" if meta else ""
    return (
        f"<details class='nd-section'{open_attr}>"
        f"<summary>{title} <span class='nd-note' style='margin-left:8px'>{tr(language, 'collapse_hint')}</span></summary>"
        f"<div class='nd-section-body'>{meta_html}{body}</div>"
        "</details>"
    )


def _page_shell(title: str, subtitle: str, body_html: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="4">
  <title>{title}</title>
  {_theme_css()}
</head>
<body style="margin:0;background:#f4f7f8;color:#17212b">
  <div style="max-width:1280px;margin:0 auto;padding:20px 16px 40px">
    <div class="nd-shell">
      <div class="nd-header">
        <div>
          <h1 class="nd-title">{title}</h1>
          <div class="nd-meta">{subtitle}</div>
        </div>
      </div>
      {body_html}
    </div>
  </div>
</body>
</html>
"""


def write_standalone_html(path: Path, title: str, subtitle: str, body_html: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_page_shell(title, subtitle, body_html), encoding="utf-8")
    return str(path)


def export_results_bundle(
    output_dir: Path,
    learner_name: str,
    parent_report_html: str,
    learner_dashboard: str,
    system_dashboard: str,
    preferred_language: str = "en",
) -> dict[str, str | list[str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    dashboard_path = output_dir / "results_dashboard.html"
    body = f"""
    <div class="nd-grid">
      {_metric_tile(tr(preferred_language, 'learner'), learner_name, tr(preferred_language, 'refresh'))}
      {_metric_tile(tr(preferred_language, 'howto'), "HTML", tr(preferred_language, 'autorefresh'))}
      {_metric_tile(tr(preferred_language, 'parent_report'), "1", tr(preferred_language, 'parent_meta'))}
      {_metric_tile(tr(preferred_language, 'system_dashboard'), "1", tr(preferred_language, 'system_meta'))}
    </div>
    {_section(tr(preferred_language, 'parent_report'), parent_report_html, preferred_language, open_=True, meta=tr(preferred_language, 'parent_meta'))}
    {_section(tr(preferred_language, 'learner_dashboard'), learner_dashboard, preferred_language, open_=True, meta=tr(preferred_language, 'learner_meta'))}
    {_section(tr(preferred_language, 'system_dashboard'), system_dashboard, preferred_language, open_=True, meta=tr(preferred_language, 'system_meta'))}
    """
    saved_path = write_standalone_html(
        dashboard_path,
        tr(preferred_language, "results_title"),
        tr(preferred_language, "results_subtitle"),
        body,
    )
    return {"results_bundle": saved_path, "files": [saved_path]}


def export_results_card(bundle: dict[str, str | list[str]], preferred_language: str = "en") -> str:
    return (
        "<div class='nd-shell'>"
        f"{_theme_css()}"
        f"{_metric_tile(tr(preferred_language, 'saved'), 'HTML', tr(preferred_language, 'saved_meta'))}"
        f"<div class='nd-note' style='margin-top:10px'><code>{bundle['results_bundle']}</code></div>"
        "</div>"
    )


def learner_dashboard_html(learner_name: str, learner_summary: dict, recent_rows: list[dict], preferred_language: str = "en") -> str:
    total_attempts = learner_summary.get("total_attempts", 0)
    correct_attempts = learner_summary.get("correct_attempts", 0)
    accuracy = int(learner_summary.get("accuracy", 0.0) * 100)
    overview = f"""
    <div class="nd-grid">
      {_metric_tile(tr(preferred_language, 'attempts'), str(total_attempts), tr(preferred_language, 'overview'))}
      {_metric_tile(tr(preferred_language, 'correct'), str(correct_attempts), tr(preferred_language, 'overview'))}
      {_metric_tile(tr(preferred_language, 'accuracy'), f"{accuracy}%", tr(preferred_language, 'overview'))}
      {_metric_tile(tr(preferred_language, 'health_strip'), str(min(len(recent_rows), 32)), tr(preferred_language, 'recent_answers'))}
    </div>
    {_health_strip(recent_rows)}
    """
    sections = (
        _section(tr(preferred_language, "overview"), overview, preferred_language, open_=True, meta=learner_name)
        + _section(tr(preferred_language, "skill_progress"), _skill_table(learner_summary.get("by_skill", []), preferred_language), preferred_language, open_=True)
        + _section(tr(preferred_language, "language_overview"), _language_panel(learner_summary.get("language_mix", []), preferred_language), preferred_language, open_=False)
        + _section(tr(preferred_language, "recent_answers"), _recent_table(recent_rows, preferred_language), preferred_language, open_=False)
    )
    return f"<div class='nd-shell'>{_theme_css()}<div class='nd-title'>{tr(preferred_language, 'learner_dashboard')}: {learner_name}</div>{sections}</div>"


def system_dashboard_html(snapshot: dict, kt_metrics_path: Path, model_status: dict, preferred_language: str = "en") -> str:
    kt_metrics = {}
    if kt_metrics_path.exists():
        kt_metrics = json.loads(kt_metrics_path.read_text(encoding="utf-8"))
    bkt_auc = kt_metrics.get("bkt_auc", "TODO")
    elo_auc = kt_metrics.get("elo_auc", "TODO")
    summary = _kt_summary(kt_metrics, preferred_language)
    overview = f"""
    <div class="nd-grid">
      {_metric_tile(tr(preferred_language, 'learners'), str(snapshot.get('learners', 0)), 'Live')}
      {_metric_tile(tr(preferred_language, 'attempts'), str(snapshot.get('attempts', 0)), 'Events')}
      {_metric_tile('BKT AUC', str(bkt_auc), 'Model')}
      {_metric_tile('Elo AUC', str(elo_auc), 'Baseline')}
    </div>
    {_health_strip(snapshot.get('recent_attempts', []))}
    """
    readiness = f"""
    <div class="nd-grid" style="grid-template-columns:repeat(2,minmax(0,1fr))">
      {_metric_tile('ASR', tr(preferred_language, 'status_ready') if model_status.get('asr_ready') else tr(preferred_language, 'status_not_ready'), model_status['asr'])}
      {_metric_tile(tr(preferred_language, 'lora'), tr(preferred_language, 'status_ready') if model_status.get('lora_ready') else tr(preferred_language, 'status_not_ready'), model_status['lora'])}
    </div>
    <div class="nd-two" style="margin-top:12px">
      <div class="nd-tile"><div class="nd-label">{tr(preferred_language, 'child_adapt')}</div><div class="nd-note" style="margin-top:8px">{model_status['adaptation']}</div></div>
      <div class="nd-tile"><div class="nd-label">{tr(preferred_language, 'offline')}</div><div class="nd-note" style="margin-top:8px">{model_status['offline']}</div></div>
    </div>
    """
    sections = (
        _section(tr(preferred_language, "overview"), overview, preferred_language, open_=True, meta=summary)
        + _section(tr(preferred_language, "skill_accuracy"), _skill_table(snapshot.get("skill_accuracy", []), preferred_language), preferred_language, open_=True)
        + _section(tr(preferred_language, "language_overview"), _language_panel(snapshot.get("language_mix", []), preferred_language), preferred_language, open_=False)
        + _section(tr(preferred_language, "recent_activity"), _recent_table(snapshot.get("recent_attempts", []), preferred_language), preferred_language, open_=False)
        + _section(tr(preferred_language, "model_readiness"), readiness, preferred_language, open_=True)
    )
    return f"<div class='nd-shell'>{_theme_css()}<div class='nd-title'>{tr(preferred_language, 'system_dashboard')}</div>{sections}</div>"
