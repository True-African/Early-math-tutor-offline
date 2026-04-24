# Local Models

Place optional local models here if you activate the advanced paths:

- `models/asr/` for a local offline ASR checkpoint such as `openai/whisper-tiny`
- `models/feedback_base/` for the small text base model used during LoRA training
- `models/lora_numeracy_adapter/` for a trained LoRA adapter and `adapter_metadata.json`

The baseline demo runs without these folders populated. If they are added later, the app will try to use them automatically.

The helper script `scripts/setup_local_models.py` downloads the default local models into these folders.
