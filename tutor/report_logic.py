from __future__ import annotations

import html
import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from tutor import SKILLS
from tutor.storage import load_mastery
from tutor.voice import (
    build_parent_voice_summary,
    gradio_file_route,
    public_file_url,
    qr_image_html,
    skill_label,
    skill_symbol,
    voice_button_html,
    write_voice_summary_page,
)


REPORT_TEXT = {
    "en": {
        "weekly_parent_report": "Weekly parent report",
        "week_of": "Week of",
        "bars_help": "Look at the bars. Green means strong. Yellow means growing. Red means help first.",
        "overall_picture": "Overall picture",
        "one_quick_look": "One quick look",
        "practice_this_week": "Practice this week",
        "times": "times",
        "strongest_now": "Strongest now",
        "celebrate": "Celebrate this skill today.",
        "help_first": "Help first",
        "start_here": "Start home practice here.",
        "simple_progress": "Simple progress bars",
        "hear_summary": "Hear the summary",
        "play_summary": "Play weekly summary",
        "voice_detail": "Short summary for a parent or caregiver.",
        "open_voice_page": "Open the voice page",
        "phone_voice": "Phone voice summary",
        "praise": "Praise",
        "praise_copy": "Smile and clap after each correct answer.",
        "count": "Count",
        "count_copy": "Count cups, beans, or steps together for one minute.",
        "repeat": "Repeat",
        "repeat_copy": "Practice the red skill first before sleeping.",
        "up": "Up",
        "watch": "Watch",
        "steady": "Steady",
        "strong": "Strong",
        "growing": "Growing",
        "help": "Help",
        "page_title": "Weekly Parent Report",
    },
    "kin": {
        "weekly_parent_report": "Raporo y'umubyeyi y'icyumweru",
        "week_of": "Icyumweru cyo ku",
        "bars_help": "Reba imirongo. Icyatsi bivuze akomeye. Umuhondo bivuze ari gutera imbere. Umutuku bivuze akeneye ubufasha mbere.",
        "overall_picture": "Ishusho rusange",
        "one_quick_look": "Rebera hamwe",
        "practice_this_week": "Kwitoza muri iki cyumweru",
        "times": "inshuro",
        "strongest_now": "Icyo akomeyeho ubu",
        "celebrate": "Mumushimire kuri iri bumenyi uyu munsi.",
        "help_first": "Tangirira hano",
        "start_here": "Muhere ku myitozo yo mu rugo hano.",
        "simple_progress": "Imirongo y'iterambere yoroshye",
        "hear_summary": "Umva incamake",
        "play_summary": "Tangira incamake y'icyumweru",
        "voice_detail": "Incamake ngufi y'umubyeyi cyangwa umurera.",
        "open_voice_page": "Fungura paji y'amajwi",
        "phone_voice": "Incamake y'amajwi kuri telefoni",
        "praise": "Shimira",
        "praise_copy": "Musekere kandi mumukomere amashyi iyo asubije neza.",
        "count": "Bara",
        "count_copy": "Mubarane ibikombe, ibishyimbo cyangwa intambwe mu munota umwe.",
        "repeat": "Subiramo",
        "repeat_copy": "Mubanze ku bumenyi buri mu mutuku mbere yo kuryama.",
        "up": "Yazamutse",
        "watch": "Mukurikirane",
        "steady": "Ari ku rugero rumwe",
        "strong": "Akomeye",
        "growing": "Arakura",
        "help": "Akeneye ubufasha",
        "page_title": "Raporo y'umubyeyi y'icyumweru",
    },
    "fr": {
        "weekly_parent_report": "Rapport parent de la semaine",
        "week_of": "Semaine du",
        "bars_help": "Regardez les barres. Le vert signifie fort. Le jaune signifie en progression. Le rouge signifie aide en priorité.",
        "overall_picture": "Vue d'ensemble",
        "one_quick_look": "Un coup d'œil",
        "practice_this_week": "Pratique cette semaine",
        "times": "fois",
        "strongest_now": "Point fort actuel",
        "celebrate": "Félicitez cette compétence aujourd'hui.",
        "help_first": "Aider d'abord",
        "start_here": "Commencez la pratique à la maison ici.",
        "simple_progress": "Barres de progression simples",
        "hear_summary": "Écouter le résumé",
        "play_summary": "Lire le résumé hebdomadaire",
        "voice_detail": "Bref résumé pour un parent ou un proche aidant.",
        "open_voice_page": "Ouvrir la page audio",
        "phone_voice": "Résumé audio sur téléphone",
        "praise": "Féliciter",
        "praise_copy": "Souriez et applaudissez après chaque bonne réponse.",
        "count": "Compter",
        "count_copy": "Comptez des tasses, des haricots ou des pas ensemble pendant une minute.",
        "repeat": "Répéter",
        "repeat_copy": "Travaillez d'abord la compétence en rouge avant de dormir.",
        "up": "En hausse",
        "watch": "À surveiller",
        "steady": "Stable",
        "strong": "Fort",
        "growing": "En progression",
        "help": "Aider",
        "page_title": "Rapport parent de la semaine",
    },
}


def rt(report: dict, key: str) -> str:
    language = (report.get("preferred_language") or "en").lower()
    return REPORT_TEXT.get(language, REPORT_TEXT["en"]).get(key, REPORT_TEXT["en"][key])


def _report_language(report: dict) -> str:
    return (report.get("preferred_language") or "en").lower()


def build_weekly_report(db_path: Path, learner_id: str, schema_path: Path, output_dir: Path | None = None) -> dict:
    # Build one simple weekly summary from the learner's attempts and current mastery estimates.
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    conn = sqlite3.connect(db_path)
    learner_row = conn.execute(
        "SELECT display_name, preferred_language FROM learners WHERE learner_id = ?",
        (learner_id,),
    ).fetchone()
    attempts = conn.execute(
        "SELECT skill, correct, created_at FROM attempts WHERE learner_id = ? ORDER BY attempt_id",
        (learner_id,),
    ).fetchall()
    conn.close()

    mastery = load_mastery(db_path, learner_id)
    week_start = date.today() - timedelta(days=date.today().weekday())
    recent = [row for row in attempts if row[2][:10] >= week_start.isoformat()]
    older = [row for row in attempts if row[2][:10] < week_start.isoformat()]

    report = {
        "learner_id": learner_id,
        "learner_name": learner_row[0] if learner_row else learner_id,
        "preferred_language": learner_row[1] if learner_row and len(learner_row) > 1 else "en",
        "week_starting": week_start.isoformat(),
        "sessions": len(recent),
        "skills": {},
        "icons_for_parent": schema.get("icons_for_parent", []),
        "voiced_summary_audio": "",
        "voiced_summary_route": "",
        "voiced_summary_public_url": "",
    }
    for skill in SKILLS:
        skill_recent = [row for row in recent if row[0] == skill]
        skill_older = [row for row in older if row[0] == skill]
        recent_avg = sum(row[1] for row in skill_recent) / len(skill_recent) if skill_recent else 0.0
        older_avg = sum(row[1] for row in skill_older) / len(skill_older) if skill_older else 0.0
        report["skills"][skill] = {
            "current": round(float(mastery.get(skill, recent_avg if recent_avg else 0.35)), 3),
            "delta": round(recent_avg - older_avg, 3),
        }

    report["voiced_summary_text"] = build_parent_voice_summary(report)
    report["voiced_summary_language"] = "rw-RW"
    if output_dir is not None:
        voice_page = write_voice_summary_page(
            output_dir=output_dir,
            learner_id=learner_id,
            week_starting=report["week_starting"],
            learner_name=report["learner_name"],
            summary_text=report["voiced_summary_text"],
            language_tag=report["voiced_summary_language"],
        )
        app_root = output_dir.parent
        report["voiced_summary_audio"] = str(voice_page)
        report["voiced_summary_route"] = gradio_file_route(voice_page, app_root)
        report["voiced_summary_public_url"] = public_file_url(voice_page, app_root)
    return report


def _trend_badge(delta: float) -> tuple[str, str]:
    if delta > 0.05:
        return "Up", "trend-up"
    if delta < -0.05:
        return "Watch", "trend-down"
    return "Steady", "trend-flat"


def _level_badge(percent: int) -> tuple[str, str]:
    if percent >= 75:
        return "Strong", "level-strong"
    if percent >= 45:
        return "Growing", "level-growing"
    return "Help", "level-help"


def _report_fragment(report: dict) -> str:
    skills = report.get("skills", {})
    ranked = sorted(skills.items(), key=lambda item: item[1].get("current", 0.0), reverse=True)
    best_skill = ranked[0][0] if ranked else "counting"
    focus_skill = ranked[-1][0] if ranked else "counting"
    average_pct = int(sum(item["current"] for item in skills.values()) / max(len(skills), 1) * 100)
    session_dots = "".join(
        "<span class='day-dot day-on'></span>" if idx < min(report.get("sessions", 0), 7) else "<span class='day-dot'></span>"
        for idx in range(7)
    )
    rows = []
    for skill, payload in skills.items():
        pct = int(payload["current"] * 100)
        trend_text, trend_class = _trend_badge(payload["delta"])
        level_text, level_class = _level_badge(pct)
        language = _report_language(report)
        trend_text = {
            "Up": rt(report, "up"),
            "Watch": rt(report, "watch"),
            "Steady": rt(report, "steady"),
        }.get(trend_text, trend_text)
        level_text = {
            "Strong": rt(report, "strong"),
            "Growing": rt(report, "growing"),
            "Help": rt(report, "help"),
        }.get(level_text, level_text)
        rows.append(
            f"""
            <div class="skill-row">
              <div class="skill-icon">{html.escape(skill_symbol(skill))}</div>
              <div class="skill-copy">
                <div class="skill-topline">
                  <div class="skill-name">{html.escape(skill_label(skill, language))}</div>
                  <div class="skill-percent">{pct}%</div>
                </div>
                <div class="skill-bar">
                  <div class="skill-fill {level_class}" style="width:{pct}%"></div>
                </div>
                <div class="skill-meta">
                  <span class="pill {trend_class}">{trend_text}</span>
                  <span class="pill {level_class}">{level_text}</span>
                </div>
              </div>
            </div>
            """
        )

    voice_panel = voice_button_html(
        report.get("voiced_summary_text", ""),
        report.get("voiced_summary_language", "rw-RW"),
        rt(report, "play_summary"),
        detail=rt(report, "voice_detail"),
    )
    voice_link = report.get("voiced_summary_route") or "#"
    qr_panel = qr_image_html(report.get("voiced_summary_public_url", ""), rt(report, "phone_voice"), _report_language(report))

    return f"""
    <div class="parent-report-shell">
      <style>
        .parent-report-shell {{
          font-family: Arial, Helvetica, sans-serif;
          background: linear-gradient(180deg, #f8f1e5 0%, #f4f7f8 100%);
          border-radius: 28px;
          padding: 20px;
          color: #18343a;
        }}
        .parent-report-card {{
          max-width: 960px;
          margin: 0 auto;
          background: #fffdf8;
          border: 2px solid #ecd8bb;
          border-radius: 28px;
          padding: 22px;
          box-shadow: 0 18px 40px rgba(15, 61, 69, 0.10);
        }}
        .parent-hero {{
          display: grid;
          grid-template-columns: 1.4fr 1fr;
          gap: 16px;
          margin-bottom: 18px;
        }}
        .hero-panel {{
          background: linear-gradient(135deg, #0f3d45 0%, #1e646c 100%);
          color: #f8fbfc;
          border-radius: 24px;
          padding: 22px;
        }}
        .hero-panel h1 {{ margin: 0 0 8px; font-size: 34px; }}
        .hero-meta {{ color: #d8ecee; font-size: 15px; line-height: 1.5; }}
        .hero-score {{
          background: #fff3df;
          color: #8b4f16;
          border-radius: 24px;
          padding: 22px;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          text-align: center;
        }}
        .score-ring {{
          width: 134px;
          height: 134px;
          border-radius: 999px;
          display: grid;
          place-items: center;
          background: conic-gradient(#ef6c2f {average_pct}%, #f5d6b5 0);
          margin-bottom: 12px;
        }}
        .score-center {{
          width: 92px;
          height: 92px;
          border-radius: 999px;
          background: #fffdf8;
          display: grid;
          place-items: center;
          font-size: 28px;
          font-weight: 800;
        }}
        .scan-grid {{
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 12px;
          margin-bottom: 18px;
        }}
        .scan-card {{
          background: #ffffff;
          border: 1px solid #ebdcc8;
          border-radius: 22px;
          padding: 16px;
        }}
        .scan-icon {{
          width: 44px;
          height: 44px;
          border-radius: 14px;
          background: #fff1de;
          color: #ef6c2f;
          display: grid;
          place-items: center;
          font-weight: 800;
          margin-bottom: 10px;
        }}
        .scan-title {{
          color: #7a6249;
          font-size: 13px;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          margin-bottom: 6px;
        }}
        .scan-big {{ font-size: 26px; font-weight: 800; }}
        .day-row {{ display: flex; gap: 6px; margin-top: 10px; }}
        .day-dot {{
          width: 14px;
          height: 14px;
          border-radius: 999px;
          background: #ead8c0;
          display: inline-block;
        }}
        .day-dot.day-on {{ background: #ef6c2f; }}
        .skills-card, .voice-grid {{
          background: #ffffff;
          border: 1px solid #ebdcc8;
          border-radius: 24px;
          padding: 18px;
        }}
        .section-title {{ margin: 0 0 14px; font-size: 24px; }}
        .skill-row {{
          display: grid;
          grid-template-columns: 54px 1fr;
          gap: 12px;
          align-items: center;
          padding: 12px 0;
          border-top: 1px solid #f1e8da;
        }}
        .skill-row:first-of-type {{ border-top: 0; padding-top: 0; }}
        .skill-icon {{
          width: 54px;
          height: 54px;
          border-radius: 18px;
          background: #fff4e5;
          color: #ef6c2f;
          display: grid;
          place-items: center;
          font-size: 20px;
          font-weight: 800;
        }}
        .skill-topline {{
          display: flex;
          justify-content: space-between;
          gap: 10px;
          align-items: center;
          margin-bottom: 8px;
        }}
        .skill-name {{ font-size: 20px; font-weight: 700; }}
        .skill-percent {{ font-size: 18px; font-weight: 800; color: #0f3d45; }}
        .skill-bar {{
          height: 18px;
          background: #f2e6d4;
          border-radius: 999px;
          overflow: hidden;
        }}
        .skill-fill {{ height: 100%; border-radius: 999px; }}
        .level-strong {{ background: #2a9d6f; color: #14553b; }}
        .level-growing {{ background: #efb33a; color: #7c5611; }}
        .level-help {{ background: #d95f5f; color: #7a2f2f; }}
        .trend-up {{ background: #ddf3e9; color: #14553b; }}
        .trend-flat {{ background: #eaf0f3; color: #50646e; }}
        .trend-down {{ background: #fbe4df; color: #8d3f37; }}
        .skill-meta {{
          display: flex;
          gap: 8px;
          margin-top: 8px;
          flex-wrap: wrap;
        }}
        .pill {{
          padding: 5px 10px;
          border-radius: 999px;
          font-size: 12px;
          font-weight: 700;
          display: inline-block;
        }}
        .voice-grid {{
          display: grid;
          grid-template-columns: 1.2fr .8fr;
          gap: 14px;
          margin-top: 16px;
        }}
        .voice-box {{
          background: #fff8ec;
          border: 1px solid #f5d6a6;
          border-radius: 18px;
          padding: 18px;
        }}
        .voice-btn {{
          border: 0;
          border-radius: 999px;
          background: #ef6c2f;
          color: #ffffff;
          font-size: 17px;
          font-weight: 800;
          padding: 14px 18px;
          cursor: pointer;
        }}
        .voice-detail {{
          margin-top: 10px;
          color: #6f6255;
          line-height: 1.45;
        }}
        .voice-link {{
          display: inline-block;
          margin-top: 12px;
          color: #0f3d45;
          font-weight: 700;
        }}
        .qr-card {{
          background: #f7fafb;
          border-radius: 20px;
          border: 1px solid #dce5ea;
          padding: 16px;
          text-align: center;
        }}
        .qr-image {{
          width: 170px;
          height: 170px;
          border-radius: 16px;
          background: #ffffff;
        }}
        .qr-title {{
          font-weight: 800;
          margin-bottom: 10px;
        }}
        .qr-copy {{
          font-size: 13px;
          color: #60707d;
          margin-top: 8px;
          line-height: 1.4;
        }}
        .coach-strip {{
          margin-top: 16px;
          background: #0f3d45;
          color: #f7fbfc;
          border-radius: 20px;
          padding: 16px 18px;
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 12px;
        }}
        .coach-step {{
          background: rgba(255,255,255,0.08);
          border-radius: 16px;
          padding: 12px;
        }}
        .coach-step b {{
          display: block;
          margin-bottom: 6px;
          font-size: 18px;
        }}
        @media (max-width: 900px) {{
          .parent-hero, .scan-grid, .voice-grid, .coach-strip {{ grid-template-columns: 1fr; }}
        }}
      </style>
      <div class="parent-report-card">
        <div class="parent-hero">
          <div class="hero-panel">
            <div class="scan-title" style="color:#f5d6b5">{html.escape(rt(report, "weekly_parent_report"))}</div>
            <h1>{html.escape(report.get("learner_name", report["learner_id"]))}</h1>
            <div class="hero-meta">
              {html.escape(rt(report, "week_of"))} {html.escape(report["week_starting"])}<br>
              {html.escape(rt(report, "bars_help"))}
            </div>
          </div>
          <div class="hero-score">
            <div class="score-ring"><div class="score-center">{average_pct}%</div></div>
            <div class="scan-title">{html.escape(rt(report, "overall_picture"))}</div>
            <div class="scan-big">{html.escape(rt(report, "one_quick_look"))}</div>
          </div>
        </div>

        <div class="scan-grid">
          <div class="scan-card">
            <div class="scan-icon">7</div>
            <div class="scan-title">{html.escape(rt(report, "practice_this_week"))}</div>
            <div class="scan-big">{report.get("sessions", 0)} {html.escape(rt(report, "times"))}</div>
            <div class="day-row">{session_dots}</div>
          </div>
          <div class="scan-card">
            <div class="scan-icon">{html.escape(skill_symbol(best_skill))}</div>
            <div class="scan-title">{html.escape(rt(report, "strongest_now"))}</div>
            <div class="scan-big">{html.escape(skill_label(best_skill, _report_language(report)))}</div>
            <div style="color:#60707d;margin-top:8px">{html.escape(rt(report, "celebrate"))}</div>
          </div>
          <div class="scan-card">
            <div class="scan-icon">{html.escape(skill_symbol(focus_skill))}</div>
            <div class="scan-title">{html.escape(rt(report, "help_first"))}</div>
            <div class="scan-big">{html.escape(skill_label(focus_skill, _report_language(report)))}</div>
            <div style="color:#60707d;margin-top:8px">{html.escape(rt(report, "start_here"))}</div>
          </div>
        </div>

        <div class="skills-card">
          <h2 class="section-title">{html.escape(rt(report, "simple_progress"))}</h2>
          {''.join(rows)}
        </div>

        <div class="voice-grid">
          <div class="skills-card">
            <h2 class="section-title">{html.escape(rt(report, "hear_summary"))}</h2>
            {voice_panel}
            <a class="voice-link" href="{html.escape(voice_link)}" target="_blank" rel="noopener noreferrer">{html.escape(rt(report, "open_voice_page"))}</a>
          </div>
          {qr_panel}
        </div>

        <div class="coach-strip">
          <div class="coach-step"><b>1. {html.escape(rt(report, "praise"))}</b> {html.escape(rt(report, "praise_copy"))}</div>
          <div class="coach-step"><b>2. {html.escape(rt(report, "count"))}</b> {html.escape(rt(report, "count_copy"))}</div>
          <div class="coach-step"><b>3. {html.escape(rt(report, "repeat"))}</b> {html.escape(rt(report, "repeat_copy"))}</div>
        </div>
      </div>
    </div>
    """


def render_parent_report_html(report: dict) -> str:
    # Render one low-literacy caregiver report fragment for the app and dashboard.
    return _report_fragment(report)


def render_parent_report_page(report: dict) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(rt(report, "page_title"))}</title>
</head>
<body style="margin:0;background:#f4f7f8">
  {_report_fragment(report)}
</body>
</html>
"""
