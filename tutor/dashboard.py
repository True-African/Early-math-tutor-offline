from __future__ import annotations

import json
from pathlib import Path

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
        "refresh": "This file refreshes after each session start or answer.",
        "autorefresh": "Browser auto-refresh: 4 seconds",
        "howto": "How to use this HTML dashboard",
        "howto_meta": "Run python demo.py, start a learner session, and submit at least one answer. This standalone file is then refreshed with the newest learner, parent, and system results.",
        "parent_report": "Parent report",
        "parent_meta": "A simple caregiver summary for the active learner.",
        "learner_dashboard": "Learner dashboard",
        "learner_meta": "Attempts, progress by skill, and language mix for the active learner.",
        "system_dashboard": "System dashboard",
        "system_meta": "Tutor-wide metrics, model readiness, and recent activity.",
        "results_title": "Tutor Results Dashboard",
        "results_subtitle": "One standalone HTML file with the latest parent report, learner dashboard, and system dashboard.",
        "saved": "HTML dashboard saved",
        "saved_meta": "Open this file directly if you want one standalone results page outside Gradio.",
        "correct": "Correct",
        "skill_progress": "Skill progress",
        "language_mix": "Language mix",
        "recent_attempts": "Recent attempts",
        "learners": "Learners",
        "skill_accuracy": "Skill accuracy",
        "recent_activity": "Recent activity",
        "model_readiness": "Model readiness",
        "child_adapt": "Child-speech adaptation",
        "lora": "LoRA language head",
        "offline": "Offline inference",
        "kt_missing": "KT evaluation has not been run yet.",
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
        "refresh": "Iyi dosiye yisubiraho nyuma yo gutangira cyangwa kohereza igisubizo.",
        "autorefresh": "Kwiyisubiraho kuri mushakisha: amasegonda 4",
        "howto": "Uko wakoresha iyi dosiye ya HTML",
        "howto_meta": "Koresha python demo.py, tangiza umwana, hanyuma wohereze nibura igisubizo kimwe. Iyi dosiye ihita yisubiraho ikerekana ibigezweho.",
        "parent_report": "Raporo y'umubyeyi",
        "parent_meta": "Incamake yoroshye y'umwana uri gukora ubu.",
        "learner_dashboard": "Aho umwana ageze",
        "learner_meta": "Inshuro zakozwe, aho ageze ku bumenyi, n'indimi yakoresheje.",
        "system_dashboard": "Aho sisitemu igeze",
        "system_meta": "Imibare rusange, uko model zihagaze, n'ibikorwa bya vuba.",
        "results_title": "Imbonerahamwe y'ibisubizo",
        "results_subtitle": "Dosiye imwe ya HTML ifite raporo y'umubyeyi, aho umwana ageze, n'ibya sisitemu.",
        "saved": "HTML yabitswe",
        "saved_meta": "Fungura iyi dosiye niba ushaka kureba ibisubizo hanze ya Gradio.",
        "correct": "Byo neza",
        "skill_progress": "Iterambere ku bumenyi",
        "language_mix": "Indimi zakoreshejwe",
        "recent_attempts": "Ibisubizo bya vuba",
        "learners": "Abana",
        "skill_accuracy": "Ukuri ku bumenyi",
        "recent_activity": "Ibikorwa bya vuba",
        "model_readiness": "Uko model zihagaze",
        "child_adapt": "Guhuza amajwi y'abana",
        "lora": "LoRA y'ururimi",
        "offline": "Gukoresha offline",
        "kt_missing": "Isuzuma rya KT ntirirakorwa.",
    },
    "fr": {
        "no_attempts": "Aucune réponse pour le moment.",
        "no_language": "Aucune donnée de langue pour le moment.",
        "no_recent": "Aucune réponse récente.",
        "skill": "Compétence",
        "progress": "Progression",
        "accuracy": "Précision",
        "attempts": "Essais",
        "answer": "Réponse",
        "language": "Langue",
        "learner": "Apprenant",
        "refresh": "Ce fichier se met à jour après chaque démarrage de session ou réponse.",
        "autorefresh": "Rafraîchissement auto du navigateur : 4 secondes",
        "howto": "Comment utiliser ce tableau HTML",
        "howto_meta": "Lancez python demo.py, démarrez un apprenant, puis envoyez au moins une réponse. Ce fichier se met ensuite à jour avec les résultats récents.",
        "parent_report": "Rapport parent",
        "parent_meta": "Un résumé simple pour le parent de l'apprenant actif.",
        "learner_dashboard": "Tableau de l'apprenant",
        "learner_meta": "Essais, progression par compétence et langues utilisées.",
        "system_dashboard": "Tableau système",
        "system_meta": "Mesures globales, état des modèles et activité récente.",
        "results_title": "Tableau des résultats du tuteur",
        "results_subtitle": "Un seul fichier HTML avec le rapport parent, le tableau de l'apprenant et le tableau système.",
        "saved": "Tableau HTML enregistré",
        "saved_meta": "Ouvrez ce fichier directement si vous voulez une page de résultats hors de Gradio.",
        "correct": "Correct",
        "skill_progress": "Progression par compétence",
        "language_mix": "Répartition des langues",
        "recent_attempts": "Réponses récentes",
        "learners": "Apprenants",
        "skill_accuracy": "Précision par compétence",
        "recent_activity": "Activité récente",
        "model_readiness": "État des modèles",
        "child_adapt": "Adaptation voix enfantine",
        "lora": "Tête de langage LoRA",
        "offline": "Inférence hors ligne",
        "kt_missing": "L'évaluation KT n'a pas encore été exécutée.",
    },
}


def tr(language: str, key: str) -> str:
    language = (language or "en").lower()
    return TEXT.get(language, TEXT["en"]).get(key, TEXT["en"].get(key, key))


def _bar(percent: int, color: str = "#2a9d8f") -> str:
    return (
        "<div style='height:12px;background:#dce5ea;border-radius:999px;overflow:hidden'>"
        f"<div style='width:{percent}%;height:12px;background:{color}'></div>"
        "</div>"
    )


def _skill_rows(rows: list[dict], language: str) -> str:
    if not rows:
        return f"<p style='color:#60707d'>{tr(language, 'no_attempts')}</p>"
    html_rows = []
    for row in rows:
        percent = int(row["accuracy"] * 100)
        html_rows.append(
            f"<tr><td>{row['skill'].replace('_', ' ').title()}</td><td>{_bar(percent)}</td><td>{percent}%</td><td>{row['attempts']}</td></tr>"
        )
    return (
        "<table style='width:100%;border-collapse:collapse'>"
        f"<thead><tr><th style='text-align:left'>{tr(language, 'skill')}</th><th style='text-align:left'>{tr(language, 'progress')}</th><th>{tr(language, 'accuracy')}</th><th>{tr(language, 'attempts')}</th></tr></thead>"
        f"<tbody>{''.join(html_rows)}</tbody></table>"
    )


def _language_chips(rows: list[dict], language: str) -> str:
    if not rows:
        return f"<span style='color:#60707d'>{tr(language, 'no_language')}</span>"
    return "".join(
        f"<span style='display:inline-block;padding:6px 10px;border-radius:999px;background:#edf5f6;color:#124f57;margin:0 6px 6px 0'>{row['language']}: {row['count']}</span>"
        for row in rows
    )


def _attempt_list(rows: list[dict], language: str) -> str:
    if not rows:
        return f"<p style='color:#60707d'>{tr(language, 'no_recent')}</p>"
    cards = []
    for row in rows[:10]:
        color = "#2a9d8f" if row["correct"] else "#d95f5f"
        answer = row.get("response_value") if row.get("response_value") is not None else row.get("response_text", "")
        cards.append(
            f"<div style='border-left:4px solid {color};padding:8px 10px;background:#fff;margin:8px 0;border-radius:8px'>"
            f"<b>{row['skill'].replace('_', ' ').title()}</b> - {row['item_id']}<br>"
            f"{tr(language, 'answer')}: {answer} - {tr(language, 'language')}: {row.get('language_detected') or 'unknown'}<br>"
            f"<span style='color:#60707d'>{row['created_at']}</span>"
            "</div>"
        )
    return "".join(cards)


def _page_shell(title: str, subtitle: str, body_html: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="4">
  <title>{title}</title>
  <style>
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #f4f7f8; color: #17212b; }}
    .page {{ max-width: 1180px; margin: 0 auto; padding: 24px 18px 40px; }}
    .page-head {{ background: #0f3d45; color: #f7fbfc; border-radius: 18px; padding: 20px 22px; margin-bottom: 18px; }}
    .page-head h1 {{ margin: 0 0 6px; font-size: 30px; }}
    .page-head p {{ margin: 0; color: #d6e7ea; }}
    .nav {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 16px; }}
    .pill {{ background:#ffffff;border:1px solid #dce5ea;padding:10px 14px;border-radius:999px; }}
    .card {{ background: #ffffff; border: 1px solid #dce5ea; border-radius: 18px; padding: 18px; margin-bottom: 16px; }}
    .meta {{ color: #60707d; font-size: 13px; margin-top: 6px; }}
    details summary {{ cursor: pointer; font-size: 22px; font-weight: 700; }}
  </style>
</head>
<body>
  <div class="page">
    <div class="page-head">
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </div>
    {body_html}
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
    # We keep one main HTML file so the repo stays tidy and the user has one clear place to look.
    output_dir.mkdir(parents=True, exist_ok=True)
    dashboard_path = output_dir / "results_dashboard.html"

    combined_body = f"""
    <div class="nav">
      <span class="pill">{tr(preferred_language, 'learner')}: {learner_name}</span>
      <span class="pill">{tr(preferred_language, 'refresh')}</span>
      <span class="pill">{tr(preferred_language, 'autorefresh')}</span>
    </div>
    <div class="card">
      <h2 style="margin-top:0">{tr(preferred_language, 'howto')}</h2>
      <p class="meta">{tr(preferred_language, 'howto_meta')}</p>
    </div>
    <details class="card" open>
      <summary>{tr(preferred_language, 'parent_report')}</summary>
      <div class="meta">{tr(preferred_language, 'parent_meta')}</div>
      {parent_report_html}
    </details>
    <details class="card" open>
      <summary>{tr(preferred_language, 'learner_dashboard')}</summary>
      <div class="meta">{tr(preferred_language, 'learner_meta')}</div>
      {learner_dashboard}
    </details>
    <details class="card" open>
      <summary>{tr(preferred_language, 'system_dashboard')}</summary>
      <div class="meta">{tr(preferred_language, 'system_meta')}</div>
      {system_dashboard}
    </details>
    """

    saved_path = write_standalone_html(
        dashboard_path,
        tr(preferred_language, "results_title"),
        tr(preferred_language, "results_subtitle"),
        combined_body,
    )
    return {"results_bundle": saved_path, "files": [saved_path]}


def export_results_card(bundle: dict[str, str | list[str]], preferred_language: str = "en") -> str:
    return f"""
    <div style="font-family:Arial,Helvetica,sans-serif;background:#ffffff;border:1px solid #dce5ea;border-radius:14px;padding:16px">
      <h3 style="margin-top:0">{tr(preferred_language, 'saved')}</h3>
      <p style="color:#60707d">{tr(preferred_language, 'saved_meta')}</p>
      <p style="margin-bottom:0"><code>{bundle['results_bundle']}</code></p>
    </div>
    """


def learner_dashboard_html(learner_name: str, learner_summary: dict, recent_rows: list[dict], preferred_language: str = "en") -> str:
    return f"""
    <div style="font-family:Arial,Helvetica,sans-serif;background:#f7fafb;padding:14px">
      <div style="background:#fff;border:1px solid #dce5ea;border-radius:14px;padding:18px">
        <h2 style="margin-top:0">{tr(preferred_language, 'learner_dashboard')}: {learner_name}</h2>
        <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px">
          <div style="border:1px solid #dce5ea;border-left:5px solid #006d77;border-radius:10px;padding:10px"><div style="color:#60707d">{tr(preferred_language, 'attempts')}</div><b style="font-size:22px">{learner_summary['total_attempts']}</b></div>
          <div style="border:1px solid #dce5ea;border-left:5px solid #2a9d8f;border-radius:10px;padding:10px"><div style="color:#60707d">{tr(preferred_language, 'correct')}</div><b style="font-size:22px">{learner_summary['correct_attempts']}</b></div>
          <div style="border:1px solid #dce5ea;border-left:5px solid #f4a261;border-radius:10px;padding:10px"><div style="color:#60707d">{tr(preferred_language, 'accuracy')}</div><b style="font-size:22px">{int(learner_summary['accuracy'] * 100)}%</b></div>
        </div>
        <h3>{tr(preferred_language, 'skill_progress')}</h3>
        {_skill_rows(learner_summary['by_skill'], preferred_language)}
        <h3>{tr(preferred_language, 'language_mix')}</h3>
        {_language_chips(learner_summary['language_mix'], preferred_language)}
        <h3>{tr(preferred_language, 'recent_attempts')}</h3>
        {_attempt_list(recent_rows, preferred_language)}
      </div>
    </div>
    """


def system_dashboard_html(snapshot: dict, kt_metrics_path: Path, model_status: dict, preferred_language: str = "en") -> str:
    kt_metrics = {}
    if kt_metrics_path.exists():
        kt_metrics = json.loads(kt_metrics_path.read_text(encoding="utf-8"))
    bkt_auc = kt_metrics.get("bkt_auc", "TODO")
    elo_auc = kt_metrics.get("elo_auc", "TODO")
    summary = kt_metrics.get("summary", tr(preferred_language, "kt_missing"))
    return f"""
    <div style="font-family:Arial,Helvetica,sans-serif;background:#f4f7f8;padding:14px">
      <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:12px">
        <div style="background:#fff;border:1px solid #dce5ea;border-left:5px solid #006d77;border-radius:10px;padding:10px"><div style="color:#60707d">{tr(preferred_language, 'learners')}</div><b style="font-size:24px">{snapshot['learners']}</b></div>
        <div style="background:#fff;border:1px solid #dce5ea;border-left:5px solid #2a9d8f;border-radius:10px;padding:10px"><div style="color:#60707d">{tr(preferred_language, 'attempts')}</div><b style="font-size:24px">{snapshot['attempts']}</b></div>
        <div style="background:#fff;border:1px solid #dce5ea;border-left:5px solid #f4a261;border-radius:10px;padding:10px"><div style="color:#60707d">BKT AUC</div><b style="font-size:24px">{bkt_auc}</b></div>
        <div style="background:#fff;border:1px solid #dce5ea;border-left:5px solid #457b9d;border-radius:10px;padding:10px"><div style="color:#60707d">Elo AUC</div><b style="font-size:24px">{elo_auc}</b></div>
      </div>
      <div style="background:#fff;border:1px solid #dce5ea;border-radius:14px;padding:18px;margin-bottom:12px">
        <h2 style="margin-top:0">{tr(preferred_language, 'system_dashboard')}</h2>
        <p style="color:#60707d">{summary}</p>
        <h3>{tr(preferred_language, 'skill_accuracy')}</h3>
        {_skill_rows(snapshot['skill_accuracy'], preferred_language)}
        <h3>{tr(preferred_language, 'language_mix')}</h3>
        {_language_chips(snapshot['language_mix'], preferred_language)}
        <h3>{tr(preferred_language, 'recent_activity')}</h3>
        {_attempt_list(snapshot['recent_attempts'], preferred_language)}
      </div>
      <div style="background:#fff;border:1px solid #dce5ea;border-radius:14px;padding:18px">
        <h2 style="margin-top:0">{tr(preferred_language, 'model_readiness')}</h2>
        <table style="width:100%;border-collapse:collapse">
          <tbody>
            <tr><th style="text-align:left">ASR</th><td>{model_status['asr']}</td></tr>
            <tr><th style="text-align:left">{tr(preferred_language, 'child_adapt')}</th><td>{model_status['adaptation']}</td></tr>
            <tr><th style="text-align:left">{tr(preferred_language, 'lora')}</th><td>{model_status['lora']}</td></tr>
            <tr><th style="text-align:left">{tr(preferred_language, 'offline')}</th><td>{model_status['offline']}</td></tr>
          </tbody>
        </table>
      </div>
    </div>
    """
