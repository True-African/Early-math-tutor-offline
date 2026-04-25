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
- prefers a quantized CTranslate2 `faster-whisper` ASR export on CPU edge devices when present
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

Activate it using the command for your terminal:

Windows Git Bash:

```bash
source venv/Scripts/activate
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
venv\Scripts\activate.bat
```

Linux, macOS, or Colab:

```bash
source venv/bin/activate
```

Install the project:

```bash
pip install -r requirements.txt
```

Online entrypoint:

```bash
python app.py
```

What this means:

- On Hugging Face Spaces, the platform reads the front matter at the top of `README.md`.
- The line `app_file: app.py` tells Hugging Face which Python file to launch.
- `app.py` is a tiny wrapper that imports the Gradio app from `demo.py` and exposes it as `app`.
- In other words, the hosted Space starts from `app.py`, but the main app logic still lives in `demo.py`.

If you want to run that same entrypoint locally, use:

```bash
python app.py
```

That launches the same Gradio app as `python demo.py`.

## Online test flow

Use this path if you want to test the app in Hugging Face without running local models.

1. Open the Hugging Face Space:

   <https://huggingface.co/spaces/Iyumva/Early-math-tutor-offline>

2. Wait for the Gradio app to load.
3. In the top area, type a learner name or choose an existing learner.
4. Click `Start or switch learner`.
5. In `Tutor Activity`, answer at least one item.
6. Open `Caregiver Report` to see the parent-facing report online.
7. Open `Learner Progress` to see learner metrics online.
8. Open `Model & Offline Notes` to see model readiness and system notes online.
9. Open `Download HTML Snapshot` if you want the generated standalone results file from the hosted app.

## Offline test flow

Use this path if you want to run the app locally with the local model setup.

1. Install the advanced dependencies:

```bash
pip install -r requirements-advanced.txt
```

2. Download the local models and prepare the quantized ASR path:

```bash
python scripts/setup_local_models.py
```

3. Start the local app:

```bash
python demo.py
```

4. Open the local Gradio app in your browser:

```text
http://127.0.0.1:7860
```

5. Type a learner name or choose an existing learner.
6. Click `Start or switch learner`.
7. Answer at least one item.
8. Open `Caregiver Report` in the running app to see the parent report offline.
9. Open `Learner Progress` in the running app to see learner metrics offline.
10. Open `Download HTML Snapshot` in the running app to reveal the exported file path.
11. Open the standalone offline report bundle directly from:

```text
outputs/results_dashboard.html
```

Offline entrypoint:

```bash
demo.py
```

Standalone parent-report script:

```bash
python parent_report.py
```

This writes:

```text
outputs/sample_parent_report.html
```

## Advanced local model activation

Convert an already-downloaded Whisper model to the int8 edge export manually:

```bash
python scripts/quantize_asr_model.py --source-model-dir models/asr --output-dir models/asr_quantized --quantization int8 --force
```

Train the small LoRA feedback adapter:

```bash
python scripts/train_lora_language_head.py --base-model models/feedback_base --epochs 2
```

This build currently uses:

- `openai/whisper-tiny` for local ASR under `models/asr/`
- a quantized CTranslate2 export under `models/asr_quantized/` for CPU edge inference
- `sshleifer/tiny-gpt2` as the small text base model under `models/feedback_base/`

Runtime note:

- the app automatically prefers `models/asr_quantized/` through `faster-whisper` when that folder exists
- because base Whisper does not expose a Kinyarwanda language token, the app uses automatic language detection for `kin` on the Whisper backends

## Reports and exported files

Keep this section in the README because it tells users exactly which generated files to open after they run the app locally.

When you start a learner session or submit an answer in the offline app, the main exported dashboard refreshes:

- [outputs/results_dashboard.html](outputs/results_dashboard.html)

That file contains:

- the parent report
- the learner dashboard
- the system dashboard
- auto-refresh every 4 seconds while it is open in the browser

Inside the Gradio app, the `Download HTML Snapshot` tab points to this same file.

If you want one standalone parent-only page, run:

```bash
python parent_report.py
```

That writes:

- [outputs/sample_parent_report.html](outputs/sample_parent_report.html)

The parent-only script now uses the most recently active learner instead of always defaulting to the first seeded learner.

The `outputs/` folder is generated-only. See [outputs/README.md](outputs/README.md) for what gets written there and how to regenerate it.

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

Build the quantized ASR edge model:

```bash
python scripts/quantize_asr_model.py --force
```

## Repo structure

| Path | Purpose |
|---|---|
| [app.py](app.py) | Hugging Face and Gradio entrypoint |
| [demo.py](demo.py) | Main tutor app |
| [parent_report.py](parent_report.py) | Weekly parent report generator |
| [assets/README.md](assets/README.md) | Notes on optional local static assets |
| [tutor/adaptive.py](tutor/adaptive.py) | Knowledge tracing and Elo baseline helpers |
| [tutor/asr_adapt.py](tutor/asr_adapt.py) | Offline ASR and child-speech augmentation helpers |
| [scripts/quantize_asr_model.py](scripts/quantize_asr_model.py) | Converts Whisper to a quantized CTranslate2 edge model |
| [tutor/lora_language.py](tutor/lora_language.py) | LoRA feedback logic with quality gate |
| [tutor/dashboard.py](tutor/dashboard.py) | Learner/system dashboard rendering and HTML export |
| [tutor/storage.py](tutor/storage.py) | Local SQLite learner storage |
| [scripts/setup_local_models.py](scripts/setup_local_models.py) | Downloads the small local ASR and text base models |
| [scripts/train_lora_language_head.py](scripts/train_lora_language_head.py) | Trains the tiny LoRA adapter |
| [scripts/run_kt_eval.py](scripts/run_kt_eval.py) | KT evaluation |
| [scripts/README.md](scripts/README.md) | Script grouping and compatibility notes |
| [docs/BRIEF_AUDIT.md](docs/BRIEF_AUDIT.md) | Requirement-by-requirement implementation audit |

## Requirement audit

A line-by-line audit of the brief is saved in:

- [docs/BRIEF_AUDIT.md](docs/BRIEF_AUDIT.md)

That file marks each requirement as:

- implemented
- partial
- not yet implemented

## Project notes

Supporting project documents now live in:

- [docs/README.md](docs/README.md)
- [docs/PROJECT_INTERPRETATION.md](docs/PROJECT_INTERPRETATION.md)
- [docs/process_log.md](docs/process_log.md)
- [docs/footprint_report.md](docs/footprint_report.md)
- [docs/SIGNED.md](docs/SIGNED.md)
- [docs/analysis/kt_eval.ipynb](docs/analysis/kt_eval.ipynb)

## Notes on repo cleanliness

The repo ignores local heavy assets and working files:

- `venv/`
- `.cache/`
- `models/asr/`
- `models/asr_quantized/`
- `models/feedback_base/`
- `models/lora_numeracy_adapter/`
- `data/local_store.sqlite`

That keeps the pushed repo clean while preserving the scripts needed to rebuild the advanced path.

## License

MIT. See [LICENSE](LICENSE).
