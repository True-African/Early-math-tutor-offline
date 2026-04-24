from __future__ import annotations

import json
from pathlib import Path


def _bar(percent: int, color: str = "#2a9d8f") -> str:
    return (
        "<div style='height:12px;background:#dce5ea;border-radius:999px;overflow:hidden'>"
        f"<div style='width:{percent}%;height:12px;background:{color}'></div>"
        "</div>"
    )


def _skill_rows(rows: list[dict]) -> str:
    if not rows:
        return "<p style='color:#60707d'>No attempts yet.</p>"
    html_rows = []
    for row in rows:
        percent = int(row["accuracy"] * 100)
        html_rows.append(
            f"<tr><td>{row['skill'].replace('_', ' ').title()}</td><td>{_bar(percent)}</td><td>{percent}%</td><td>{row['attempts']}</td></tr>"
        )
    return (
        "<table style='width:100%;border-collapse:collapse'>"
        "<thead><tr><th style='text-align:left'>Skill</th><th style='text-align:left'>Progress</th><th>Accuracy</th><th>Attempts</th></tr></thead>"
        f"<tbody>{''.join(html_rows)}</tbody></table>"
    )


def _language_chips(rows: list[dict]) -> str:
    if not rows:
        return "<span style='color:#60707d'>No language data yet.</span>"
    return "".join(
        f"<span style='display:inline-block;padding:6px 10px;border-radius:999px;background:#edf5f6;color:#124f57;margin:0 6px 6px 0'>{row['language']}: {row['count']}</span>"
        for row in rows
    )


def _attempt_list(rows: list[dict]) -> str:
    if not rows:
        return "<p style='color:#60707d'>No recent attempts yet.</p>"
    cards = []
    for row in rows[:10]:
        color = "#2a9d8f" if row["correct"] else "#d95f5f"
        answer = row.get("response_value") if row.get("response_value") is not None else row.get("response_text", "")
        cards.append(
            f"<div style='border-left:4px solid {color};padding:8px 10px;background:#fff;margin:8px 0;border-radius:8px'>"
            f"<b>{row['skill'].replace('_', ' ').title()}</b> - {row['item_id']}<br>"
            f"Answer: {answer} - Language: {row.get('language_detected') or 'unknown'}<br>"
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
) -> dict[str, str | list[str]]:
    # We keep one main HTML file so the repo stays tidy and the user has one clear place to look.
    output_dir.mkdir(parents=True, exist_ok=True)
    dashboard_path = output_dir / "results_dashboard.html"

    combined_body = f"""
    <div class="nav">
      <span class="pill">Learner: {learner_name}</span>
      <span class="pill">This file refreshes after each session start or answer.</span>
      <span class="pill">Browser auto-refresh: 4 seconds</span>
    </div>
    <div class="card">
      <h2 style="margin-top:0">How to use this HTML dashboard</h2>
      <p class="meta">Run <code>python demo.py</code>, start a learner session, and submit at least one answer. This standalone file is then refreshed with the newest learner, parent, and system results.</p>
    </div>
    <details class="card" open>
      <summary>Parent report</summary>
      <div class="meta">A simple caregiver summary for the active learner.</div>
      {parent_report_html}
    </details>
    <details class="card" open>
      <summary>Learner dashboard</summary>
      <div class="meta">Attempts, progress by skill, and language mix for the active learner.</div>
      {learner_dashboard}
    </details>
    <details class="card" open>
      <summary>System dashboard</summary>
      <div class="meta">Tutor-wide metrics, model readiness, and recent activity.</div>
      {system_dashboard}
    </details>
    """

    saved_path = write_standalone_html(
        dashboard_path,
        "Tutor Results Dashboard",
        "One standalone HTML file with the latest parent report, learner dashboard, and system dashboard.",
        combined_body,
    )
    return {"results_bundle": saved_path, "files": [saved_path]}


def export_results_card(bundle: dict[str, str | list[str]]) -> str:
    return f"""
    <div style="font-family:Arial,Helvetica,sans-serif;background:#ffffff;border:1px solid #dce5ea;border-radius:14px;padding:16px">
      <h3 style="margin-top:0">HTML dashboard saved</h3>
      <p style="color:#60707d">Open this file directly if you want one standalone results page outside Gradio.</p>
      <p style="margin-bottom:0"><code>{bundle['results_bundle']}</code></p>
    </div>
    """


def learner_dashboard_html(learner_name: str, learner_summary: dict, recent_rows: list[dict]) -> str:
    return f"""
    <div style="font-family:Arial,Helvetica,sans-serif;background:#f7fafb;padding:14px">
      <div style="background:#fff;border:1px solid #dce5ea;border-radius:14px;padding:18px">
        <h2 style="margin-top:0">Learner dashboard: {learner_name}</h2>
        <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px">
          <div style="border:1px solid #dce5ea;border-left:5px solid #006d77;border-radius:10px;padding:10px"><div style="color:#60707d">Attempts</div><b style="font-size:22px">{learner_summary['total_attempts']}</b></div>
          <div style="border:1px solid #dce5ea;border-left:5px solid #2a9d8f;border-radius:10px;padding:10px"><div style="color:#60707d">Correct</div><b style="font-size:22px">{learner_summary['correct_attempts']}</b></div>
          <div style="border:1px solid #dce5ea;border-left:5px solid #f4a261;border-radius:10px;padding:10px"><div style="color:#60707d">Accuracy</div><b style="font-size:22px">{int(learner_summary['accuracy'] * 100)}%</b></div>
        </div>
        <h3>Skill progress</h3>
        {_skill_rows(learner_summary['by_skill'])}
        <h3>Language mix</h3>
        {_language_chips(learner_summary['language_mix'])}
        <h3>Recent attempts</h3>
        {_attempt_list(recent_rows)}
      </div>
    </div>
    """


def system_dashboard_html(snapshot: dict, kt_metrics_path: Path, model_status: dict) -> str:
    kt_metrics = {}
    if kt_metrics_path.exists():
        kt_metrics = json.loads(kt_metrics_path.read_text(encoding="utf-8"))
    bkt_auc = kt_metrics.get("bkt_auc", "TODO")
    elo_auc = kt_metrics.get("elo_auc", "TODO")
    summary = kt_metrics.get("summary", "KT evaluation has not been run yet.")
    return f"""
    <div style="font-family:Arial,Helvetica,sans-serif;background:#f4f7f8;padding:14px">
      <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:12px">
        <div style="background:#fff;border:1px solid #dce5ea;border-left:5px solid #006d77;border-radius:10px;padding:10px"><div style="color:#60707d">Learners</div><b style="font-size:24px">{snapshot['learners']}</b></div>
        <div style="background:#fff;border:1px solid #dce5ea;border-left:5px solid #2a9d8f;border-radius:10px;padding:10px"><div style="color:#60707d">Attempts</div><b style="font-size:24px">{snapshot['attempts']}</b></div>
        <div style="background:#fff;border:1px solid #dce5ea;border-left:5px solid #f4a261;border-radius:10px;padding:10px"><div style="color:#60707d">BKT AUC</div><b style="font-size:24px">{bkt_auc}</b></div>
        <div style="background:#fff;border:1px solid #dce5ea;border-left:5px solid #457b9d;border-radius:10px;padding:10px"><div style="color:#60707d">Elo AUC</div><b style="font-size:24px">{elo_auc}</b></div>
      </div>
      <div style="background:#fff;border:1px solid #dce5ea;border-radius:14px;padding:18px;margin-bottom:12px">
        <h2 style="margin-top:0">System dashboard</h2>
        <p style="color:#60707d">{summary}</p>
        <h3>Skill accuracy</h3>
        {_skill_rows(snapshot['skill_accuracy'])}
        <h3>Language mix</h3>
        {_language_chips(snapshot['language_mix'])}
        <h3>Recent activity</h3>
        {_attempt_list(snapshot['recent_attempts'])}
      </div>
      <div style="background:#fff;border:1px solid #dce5ea;border-radius:14px;padding:18px">
        <h2 style="margin-top:0">Model readiness</h2>
        <table style="width:100%;border-collapse:collapse">
          <tbody>
            <tr><th style="text-align:left">ASR</th><td>{model_status['asr']}</td></tr>
            <tr><th style="text-align:left">Child-speech adaptation</th><td>{model_status['adaptation']}</td></tr>
            <tr><th style="text-align:left">LoRA language head</th><td>{model_status['lora']}</td></tr>
            <tr><th style="text-align:left">Offline inference</th><td>{model_status['offline']}</td></tr>
          </tbody>
        </table>
      </div>
    </div>
    """
