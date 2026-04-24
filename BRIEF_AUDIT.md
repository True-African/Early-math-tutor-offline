# Brief Audit

This file checks the current build against the task brief line by line and marks what is implemented now, what is partial, and what is still missing.

Status labels:

- `Implemented`
- `Partial`
- `Not yet implemented`

## Brief-level context

| Brief item | Status | Notes |
|---|---|---|
| Offline early-math tutor for ages 5-9 | Implemented | The current app teaches counting, number sense, addition, subtraction, and word problems. |
| Works fully offline at inference | Implemented | The tutor, local storage, local ASR model path, and local LoRA path all run without external API calls at inference. |
| Handles multilingual and code-switched input | Partial | EN / FR / KIN / mix detection is implemented. The reply follows dominant language, but the mixed-language embedding behavior for number words is still simplified. |
| Live Defense readiness | Implemented | Repo is runnable, auditable, and now has a requirement-by-requirement audit file. |

## Provided materials

| Brief item | Status | Notes |
|---|---|---|
| Use the seed folder files | Implemented | Seed files are copied into `data/seed/` and used by the app. |
| Real ASR seeds: Whisper Tiny or MMS | Implemented | Local ASR path is wired and currently uses `openai/whisper-tiny`. |
| Real child speech datasets for adaptation | Partial | The augmentation script is implemented, but the repo does not yet bundle approved real child audio subsets. |
| Real LLM seed for language head | Partial | The live local path uses `sshleifer/tiny-gpt2` for practicality. This is lighter than the brief's suggested Phi-3 or TinyLlama path. |

## Synthetic data generator specs

| Brief item | Status | Notes |
|---|---|---|
| Author full curriculum with at least 60 items | Implemented | `data/generated_curriculum.json` contains 60 items. |
| Render TTS lines locally with Coqui-TTS or Piper | Not yet implemented | The tutor uses text prompts and local ASR, but local TTS rendering and cached audio output are not yet built. |
| Generate child-voiced utterances by pitch shift and classroom noise | Partial | `scripts/adapt_child_asr.py` and `tutor/asr_adapt.py` implement pitch, tempo, and noise augmentation, but real dataset ingestion still needs to be completed. |

## Task 1 - On-device inference pipeline

| Brief item | Status | Notes |
|---|---|---|
| Visual item presentation | Implemented | Visual items are rendered inside the main tutor interface. |
| Audio item presentation | Partial | Microphone response is implemented, but spoken feedback audio in the learner's language is not yet generated locally. |
| Voice or tap response | Implemented | The app supports tap answers, typed answers, and microphone capture. |
| Scoring | Implemented | Answers are scored and stored locally. |
| Feedback audio in learner's language | Not yet implemented | Feedback text is multilingual, but audio playback is not yet added. |
| Latency target under 2.5 seconds | Partial | The tutor flow is lightweight, but a measured latency report is still needed for this exact target. |

## Task 2 - Knowledge tracing

| Brief item | Status | Notes |
|---|---|---|
| Implement BKT or DKT | Implemented | BKT is implemented in `tutor/adaptive.py`. |
| Compare to Elo baseline | Implemented | Elo baseline is implemented and compared in the KT evaluation script. |
| Report AUC of next-response correctness prediction | Implemented | `outputs/kt_metrics.json` reports BKT AUC and Elo AUC. |

## Task 3 - Language head fine-tuning

| Brief item | Status | Notes |
|---|---|---|
| Fine-tune with QLoRA / LoRA | Implemented | A small LoRA adapter is trained and stored locally. |
| Merge adapters | Not yet implemented | The current repo keeps the adapter separate. |
| Quantise to int4 with GGUF or AWQ | Not yet implemented | No merged int4 `gguf` or `awq` model is produced yet. |

## Task 4 - Multilingual and code-switching

| Brief item | Status | Notes |
|---|---|---|
| Detect KIN / FR / EN / mix | Implemented | Language detection is implemented in `tutor/language.py`. |
| Reply in dominant language | Implemented | The tutor chooses a dominant reply language. |
| For mixed responses, mirror dominant language and embed second language number words | Partial | The current response handling is simpler than the full requested behavior. |

## Task 5 - Visual grounding

| Brief item | Status | Notes |
|---|---|---|
| At least one item type requires counting objects in a rendered image | Implemented | Counting scenes are rendered from the visual id. |
| Use a small detector or a blob counter baseline | Partial | The current baseline uses rendered scene metadata rather than a standalone blob-counting model. |

## Task 6 - Local progress store and privacy

| Brief item | Status | Notes |
|---|---|---|
| Encrypted SQLite | Not yet implemented | The repo uses SQLite, but it is not encrypted yet. |
| Minimal weekly parent report | Implemented | `parent_report.py` and the parent-report tab are working. |
| Differential privacy sync with documented epsilon budget | Not yet implemented | This is documented as a future path, but not yet built. |

## Task 7 - Footprint

| Brief item | Status | Notes |
|---|---|---|
| Total on-device footprint at or below 75 MB excluding TTS cache | Partial | The `tutor/` package is tiny, but a full measured end-to-end packaged footprint including local models still needs to be documented more explicitly. |
| Provide a `du -sh tutor/` line in README | Implemented | README now includes the `du -sh tutor/` line. |

## Deliverables

| Brief item | Status | Notes |
|---|---|---|
| `tutor/` package | Implemented | Present. |
| `model.onnx` or `.gguf` in tutor package | Not yet implemented | The project currently uses local Hugging Face model folders and a LoRA adapter instead. |
| `curriculum_loader.py` | Implemented | Present. |
| `adaptive.py` with KT model | Implemented | Present. |
| `asr_adapt.py` | Implemented | Present. |
| `demo.py` Gradio app with microphone input | Implemented | Present and working. |
| `parent_report.py` | Implemented | Present and working. |
| `footprint_report.md` | Implemented | Present. |
| `kt_eval.ipynb` | Implemented | Present. |
| `process_log.md` | Implemented | Present. |

## Hosting and reproducibility

| Brief item | Status | Notes |
|---|---|---|
| Public code repo | Ready | README now includes GitHub and Hugging Face clone links. |
| Model hosting link | Ready | Hugging Face Space link is now documented. |
| README reproducible in 2 commands or fewer on CPU | Partial | `pip install -r requirements.txt` and `python demo.py` works for the main app. Advanced model activation takes extra commands. |
| LICENSE file | Implemented | Present. |

## Technical constraints

| Brief item | Status | Notes |
|---|---|---|
| CPU-only | Implemented | Current setup is CPU-only. |
| Fully offline at inference | Implemented | No external API calls are used during inference. |
| No dark patterns | Implemented | The app does not include streak loss, purchases, or trackers. |

## Product and business adaptation

| Brief item | Status | Notes |
|---|---|---|
| First 90 seconds for a 6-year-old Kinyarwanda-speaking learner | Implemented | Reflected in the tutor intro and scenario card. |
| Silence for 10 seconds behavior | Implemented in design | Documented in the scenario card, though not yet a timed automatic event in code. |
| Shared tablet across 3 children | Implemented | Learner switching and local profiles are built. |
| Preserve privacy locally and survive reboot | Partial | Local profiles survive reboot. Privacy separation is basic; encryption is still missing. |
| One-page weekly parent report understandable in 60 seconds | Implemented | Parent report uses simple bars and trends. |
| One voiced summary via QR if needed | Not yet implemented | The report has a placeholder path, but not a working QR-to-audio feature. |

## Optional stretch goal

| Brief item | Status | Notes |
|---|---|---|
| Dyscalculia early-warning after repeated plateau | Not yet implemented | Not added yet. |

## Important contradictions in the brief

| Brief item | Status | Notes |
|---|---|---|
| No formal submission today | Contradiction | The PDF says there is no formal submission today, but later scoring text still mentions a video. Your current workflow is set up for hosted repo inspection either way. |
| README plus 4-minute video in scoring table | Contradiction | The PDF says no formal submission and no 4-minute video today, but the scoring table still mentions one. |

## Honest summary

The current repo is strongest on:

- offline adaptive tutoring
- local learner storage
- multilingual handling
- Gradio demo and dashboards
- HTML export for easy review
- local ASR activation
- measured KT evaluation

The biggest remaining gaps against the brief are:

- encrypted SQLite
- local feedback audio / TTS
- LoRA merge plus int4 quantisation
- documented differential privacy sync
- a stronger visual-grounding baseline than scene-metadata counting
