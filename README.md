---
title: Early Math Tutor Offline
sdk: gradio
app_file: app.py
short_description: Offline adaptive math tutor for ages 5-9.
---

# Early Math Tutor Offline

Early Math Tutor Offline is a child-friendly numeracy tutor for ages 5 to 9. It teaches counting, number sense, addition, subtraction, and simple word problems through visuals, adaptive practice, multilingual prompts, microphone or tap response, and a simple weekly parent report.

## Hosted links

- GitHub: <https://github.com/True-African/Early-math-tutor-offline.git>
- Hugging Face Space: <https://huggingface.co/spaces/Iyumva/Early-math-tutor-offline>

Clone from GitHub:

```bash
git clone https://github.com/True-African/Early-math-tutor-offline.git
cd Early-math-tutor-offline
```

Clone from Hugging Face:

```bash
git clone https://huggingface.co/spaces/Iyumva/Early-math-tutor-offline
cd Early-math-tutor-offline
```

## What this project currently does

- runs offline at inference time
- uses Bayesian Knowledge Tracing to choose the next item
- supports Kinyarwanda, English, French, and mixed response detection
- supports tap response and microphone capture
- loads a local Whisper Tiny ASR model when present
- loads a local LoRA feedback adapter when present
- falls back to simple template feedback when the tiny language model output is weak
- stores learner progress locally in SQLite
- shows learner, parent, and system dashboards in Gradio
- exports one standalone HTML results dashboard to `outputs/results_dashboard.html`

## Current measured results

- BKT AUC: `0.6013`
- Elo baseline AUC: `0.6180`
- Replay size: `2880` answer events across `120` synthetic learners

Footprint note:

```bash
du -sh tutor/
```

Current measured package size for `tutor/`:

- about `0.111 MB`

## Quick start

Create a virtual environment:

```powershell
python -m venv venv
```

Activate it in your shell:

```powershell
.\venv\Scripts\Activate.ps1
```

```cmd
venv\Scripts\activate.bat
```

```bash
source venv/Scripts/activate
```

Install the project and run the tutor:

```bash
pip install -r requirements.txt
python demo.py
```

Then open the local Gradio URL shown in the terminal.

## Advanced local model activation

Install the advanced dependencies:

```bash
pip install -r requirements-advanced.txt
```

Download the small local models used by the advanced path:

```bash
python scripts/setup_local_models.py
```

Train the small LoRA feedback adapter:

```bash
python scripts/train_lora_language_head.py --base-model models/feedback_base --epochs 2
```

This build currently uses:

- `openai/whisper-tiny` for local ASR under `models/asr/`
- `sshleifer/tiny-gpt2` as the small text base model under `models/feedback_base/`

## How to see results in HTML

When you start a learner session or submit an answer, the app refreshes:

- [outputs/results_dashboard.html](outputs/results_dashboard.html)

That file contains:

- the parent report
- the learner dashboard
- the system dashboard
- auto-refresh every 4 seconds while it is open in the browser

Inside the Gradio app, the **HTML Results** tab also points to this same file.

## Useful commands

Generate the expanded curriculum:

```bash
python scripts/generate_curriculum.py
```

Run KT evaluation:

```bash
python scripts/run_kt_eval.py
```

Seed one learner for screenshots or report generation:

```bash
python scripts/seed_demo_data.py
```

Generate the weekly parent report:

```bash
python parent_report.py
```

Prepare child-speech augmented manifest:

```bash
python scripts/adapt_child_asr.py
```

## Repo structure

| Path | Purpose |
|---|---|
| [app.py](app.py) | Hugging Face and Gradio entrypoint |
| [demo.py](demo.py) | Main tutor app |
| [parent_report.py](parent_report.py) | Weekly parent report generator |
| [tutor/adaptive.py](tutor/adaptive.py) | Knowledge tracing and Elo baseline helpers |
| [tutor/asr_adapt.py](tutor/asr_adapt.py) | Offline ASR and child-speech augmentation helpers |
| [tutor/lora_language.py](tutor/lora_language.py) | LoRA feedback logic with quality gate |
| [tutor/dashboard.py](tutor/dashboard.py) | Learner/system dashboard rendering and HTML export |
| [tutor/storage.py](tutor/storage.py) | Local SQLite learner storage |
| [scripts/setup_local_models.py](scripts/setup_local_models.py) | Downloads the small local ASR and text base models |
| [scripts/train_lora_language_head.py](scripts/train_lora_language_head.py) | Trains the tiny LoRA adapter |
| [scripts/run_kt_eval.py](scripts/run_kt_eval.py) | KT evaluation |
| [BRIEF_AUDIT.md](BRIEF_AUDIT.md) | Requirement-by-requirement implementation audit |

## Requirement audit

A line-by-line audit of the brief is saved in:

- [BRIEF_AUDIT.md](BRIEF_AUDIT.md)

That file marks each requirement as:

- implemented
- partial
- not yet implemented

## Notes on repo cleanliness

The repo ignores local heavy assets and working files:

- `venv/`
- `.cache/`
- `models/asr/`
- `models/feedback_base/`
- `models/lora_numeracy_adapter/`
- `data/local_store.sqlite`

That keeps the pushed repo clean while preserving the scripts needed to rebuild the advanced path.

## License

MIT. See [LICENSE](LICENSE).
