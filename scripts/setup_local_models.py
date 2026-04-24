from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import snapshot_download

try:
    from quantize_asr_model import convert_asr_model
except Exception:  # pragma: no cover - optional dependency
    convert_asr_model = None


ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
ASR_DIR = MODELS_DIR / "asr"
QUANTIZED_ASR_DIR = MODELS_DIR / "asr_quantized"
FEEDBACK_BASE_DIR = MODELS_DIR / "feedback_base"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download small local models for offline ASR and LoRA feedback.")
    parser.add_argument("--asr-model", default="openai/whisper-tiny", help="ASR model id to download.")
    parser.add_argument("--feedback-model", default="sshleifer/tiny-gpt2", help="Small text model id to download for LoRA training.")
    parser.add_argument(
        "--asr-quantization",
        default="int8",
        choices=["int8", "int8_float32", "int8_float16", "int8_bfloat16", "int16", "float16", "float32"],
        help="Quantization scheme for the CTranslate2 edge ASR export.",
    )
    parser.add_argument("--skip-asr-quantization", action="store_true", help="Download the HF ASR model without building the quantized edge export.")
    return parser.parse_args()


def download_model(repo_id: str, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=repo_id,
        local_dir=str(target_dir),
    )


def main() -> None:
    args = parse_args()
    download_model(args.asr_model, ASR_DIR)
    print(f"Downloaded ASR model to {ASR_DIR}")
    if args.skip_asr_quantization:
        print("Skipped quantized ASR export.")
    elif convert_asr_model is None:
        print(
            "Skipped quantized ASR export because CTranslate2 is not installed. "
            "Install requirements-advanced.txt and run python scripts/quantize_asr_model.py later."
        )
    else:
        saved_dir = convert_asr_model(ASR_DIR, QUANTIZED_ASR_DIR, quantization=args.asr_quantization, force=True)
        print(f"Saved quantized ASR model to {saved_dir}")
    download_model(args.feedback_model, FEEDBACK_BASE_DIR)
    print(f"Downloaded feedback base model to {FEEDBACK_BASE_DIR}")


if __name__ == "__main__":
    main()
