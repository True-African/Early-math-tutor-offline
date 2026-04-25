# Generated Outputs

This folder is for generated artifacts only.

The app and helper scripts write files here during local use, for example:

- `results_dashboard.html`
- `sample_parent_report.html`
- `kt_metrics.json`
- `kt_replay.csv`
- `voice/`

These files are intentionally not tracked in Git so the repo stays clean.

To regenerate common outputs:

```bash
python demo.py
python parent_report.py
python scripts/run_kt_eval.py
```
