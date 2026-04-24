# Project Interpretation

This file saves the current interpretation of the offline early-math tutor task and the conservative baseline we should build first.

## Part A — Challenge Interpretation

### Plain-language summary

Build a small offline tutor for children aged 5 to 9 that teaches early numeracy through visuals, audio-friendly prompts, and simple interaction. The tutor should adjust to the learner's level, support English, French, Kinyarwanda, and mixed responses, work on a low-cost shared device, and generate a simple weekly parent report.

### What the provided seed files already contain

- `curriculum_seed.json`: starter numeracy items across counting, number sense, addition, subtraction, and word problems.
- `diagnostic_probes_seed.csv`: starter probes for fast learner placement.
- `child_utt_sample_seed.csv`: sample utterance manifest rows for child responses.
- `parent_report_schema.json`: the structure expected for the weekly parent report.
- `child_utt_index.md`: references for public speech sources and synthetic child-speech generation.

### Required deliverables

- `tutor/` package
- `demo.py`
- `parent_report.py`
- `footprint_report.md`
- `kt_eval.ipynb`
- `process_log.md`
- `SIGNED.md`
- public code repo
- hosted model or checkpoint link if produced
- data or generator script
- reproducible `README.md`
- `LICENSE`

### Hard technical constraints

- CPU-only
- fully offline at inference
- total app footprint at or below 75 MB, excluding TTS cache
- per-cycle response latency below 2.5 seconds
- child-friendly and low-literacy design

### Required product adaptation

- design the first 90 seconds for a 6-year-old Kinyarwanda-speaking learner
- support a shared tablet across 3 children
- preserve privacy locally and recover gracefully after reboot
- produce a weekly parent report understandable in about 60 seconds
- adapt for multilingual, low-bandwidth, and non-smartphone use

### What evaluators are likely to care about most

1. Is the demo easy to run?
2. Does the tutor actually adapt in a simple, defensible way?
3. Is the local-context adaptation concrete?
4. Is the repo easy to inspect during live defense?
5. Are the trade-offs honest and explainable?

### Current working assumption

Assume formal submission is required and keep the repo, hosted artefacts, and supporting files ready for inspection.

## Part B — Can a non-ML builder do this?

Yes, but only with a conservative baseline.

### Easier parts

- repo structure and README
- curriculum expansion
- Gradio interface
- tap-first learner interaction
- local SQLite progress store
- parent report
- shared-device workflow

### Moderate parts

- Bayesian Knowledge Tracing
- simple language detection
- replay-style evaluation
- simple visual counting task

### Hardest parts

- child speech adaptation
- LoRA fine-tuning and quantization
- strict footprint control with heavier models
- polished multilingual voice pipeline

### Safe strategy

Build a product-first tutor:

- tap-first, microphone optional
- BKT instead of DKT
- rule-based language detection first
- simple rendered-object counting
- local SQLite progress storage
- small, explainable baseline before any advanced model work

### What not to overbuild

- custom deep learning from scratch
- large multimodal models unless clearly necessary
- online dependencies at runtime
- game mechanics that distract from the brief

## Part C — Conservative Baseline

### Child-facing demo

- Gradio interface
- large visual prompt
- large tap choices
- optional typed or spoken-word text input

### Adaptive sequencing

- 5-probe warm start
- BKT mastery state per skill
- next item chosen from weakest skill first

### Local scoring

- exact integer scoring
- simple number-word normalization for EN / FR / KIN

### Local progress store

- SQLite database
- separate learner profiles
- session and attempt history

### Weekly parent report

- one-page HTML summary
- icons, simple bars, and one short voiced-summary field path

### Multilingual UX

- Kinyarwanda-first for the first learner flow
- dominant-language response logic
- simple mixed-language handling

### Visual counting

- pre-rendered object scenes
- count inferred from metadata or simple object count baseline

### Offline-first behavior

- all curriculum and logic local
- no runtime API calls

### Footprint discipline

- keep heavy speech or language models optional
- do not block the baseline on LoRA or ASR adaptation

## Part D — Proposed outward-facing names

- Repo: `early-math-tutor-offline`
- Hugging Face Space: `Iyumva/early-math-tutor-offline`
- Model or checkpoint: `Iyumva/early-math-tutor-lite`

### Short description

Offline early numeracy tutor for ages 5 to 9 with adaptive practice, multilingual support, and simple parent progress summaries.

## Part E — Build order

1. Get the Gradio tutor running with the seed curriculum.
2. Expand the curriculum to 60 or more items.
3. Add BKT mastery tracking.
4. Add SQLite learner storage.
5. Add parent report generation.
6. Add multilingual response handling.
7. Add replay evaluation and footprint notes.
8. Treat ASR adaptation and LoRA as optional only if time remains.
