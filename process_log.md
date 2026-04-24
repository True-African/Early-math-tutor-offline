# process_log.md

Candidate: [FULL NAME]
Project: Early Math Tutor Offline
Date: 24 April 2026

## Timeline

| Time | Work done |
|---|---|
| 00:00-00:30 | Read brief, inspected seed files, created repo scaffold |
| 00:30-01:00 | Expanded curriculum and built the starter learner flow |
| 01:00-01:45 | Added adaptive sequencing and local scoring |
| 01:45-02:20 | Added SQLite learner storage and learner switching |
| 02:20-02:50 | Built weekly parent report |
| 02:50-03:20 | Added multilingual handling and offline behavior notes |
| 03:20-03:45 | Added evaluation notebook and footprint notes |
| 03:45-04:00 | Final run checks and documentation cleanup |
| Follow-up polish | Activated local ASR and tiny LoRA paths, added single-file HTML results dashboard, updated README links, and audited the brief line by line |

## Declared LLM / Assistant Tools

| Tool | Purpose | What I changed or verified myself |
|---|---|---|
| ChatGPT / Codex | Planning, code scaffolding, review, documentation, and requirement audit | I ran the code, checked the outputs, edited assumptions, and verified the final repo content myself |

## Three Sample Prompts I Used

1. "Interpret the offline math tutor brief and recommend a conservative baseline."
2. "Help me structure an explainable BKT-first tutor for children aged 5 to 9."
3. "Help me design a low-literacy weekly parent report for a shared offline tablet."

## One Discarded Prompt

Discarded prompt: "Generate a full advanced model pipeline that I can submit without understanding."

Reason: It would not be defensible during live review.

## Hardest Decision

The hardest decision was choosing which advanced parts to defer so the final system remained small, runnable, and explainable.
