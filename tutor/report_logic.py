from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from tutor import SKILLS
from tutor.storage import load_mastery


def build_weekly_report(db_path: Path, learner_id: str, schema_path: Path) -> dict:
    # Build one simple weekly summary from the learner's attempts and current mastery estimates.
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    conn = sqlite3.connect(db_path)
    learner_row = conn.execute(
        "SELECT display_name FROM learners WHERE learner_id = ?",
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
        "week_starting": week_start.isoformat(),
        "sessions": len(recent),
        "skills": {},
        "icons_for_parent": schema.get("icons_for_parent", []),
        "voiced_summary_audio": "",
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
    return report


def render_parent_report_html(report: dict) -> str:
    # Render the report as one clear page that a caregiver can scan quickly.
    rows = []
    for skill, payload in report["skills"].items():
        pct = int(payload["current"] * 100)
        delta = payload["delta"]
        icon = "⬆" if delta > 0.05 else ("⬇" if delta < -0.05 else "→")
        rows.append(
            f"<tr><td>{skill.replace('_', ' ').title()}</td><td>{icon}</td>"
            f"<td><div style='height:10px;background:#d9e2e8;border-radius:999px;overflow:hidden'>"
            f"<div style='width:{pct}%;height:10px;background:#2a9d8f'></div></div></td>"
            f"<td>{pct}%</td></tr>"
        )
    return f"""
    <html>
    <body style="font-family:Arial,Helvetica,sans-serif;background:#f7fafb;padding:24px">
      <div style="max-width:780px;margin:0 auto;background:#fff;border:1px solid #d9e2e8;border-radius:14px;padding:20px">
        <h1 style="margin-top:0">Weekly Parent Report</h1>
        <p><b>Learner:</b> {report.get('learner_name', report['learner_id'])}<br>
        <b>Week starting:</b> {report['week_starting']}<br>
        <b>Sessions:</b> {report['sessions']}</p>
        <p>This report uses simple arrows and bars so a parent can understand progress quickly.</p>
        <table style="width:100%;border-collapse:collapse">
          <thead><tr><th style="text-align:left">Skill</th><th>Trend</th><th style="text-align:left">Progress</th><th>Level</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
        <p style="margin-top:16px"><b>Simple summary:</b> Keep practicing the weakest skill first, and praise the child after every correct answer.</p>
      </div>
    </body>
    </html>
    """
