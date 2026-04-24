from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tutor.report_logic import build_weekly_report, render_parent_report_html
from tutor.storage import list_learners

DB_PATH = ROOT / "data" / "local_store.sqlite"
SCHEMA_PATH = ROOT / "data" / "seed" / "parent_report_schema.json"
OUTPUT_PATH = ROOT / "outputs" / "sample_parent_report.html"


def main() -> None:
    # This small script creates one parent-facing HTML page from the local learner database.
    learners = list_learners(DB_PATH)
    if not learners:
        print("No learners found yet. Run demo.py and answer at least one item first.")
        return
    learner_id, learner_name = learners[0]
    report = build_weekly_report(DB_PATH, learner_id, SCHEMA_PATH)
    html = render_parent_report_html(report)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Saved parent report for {learner_name} to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
