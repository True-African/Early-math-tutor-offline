from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import snapshot_download


ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
ASR_DIR = MODELS_DIR / "asr"
FEEDBACK_BASE_DIR = MODELS_DIR / "feedback_base"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download small local models for offline ASR and LoRA feedback.")
    parser.add_argument("--asr-model", default="openai/whisper-tiny", help="ASR model id to download.")
    parser.add_argument("--feedback-model", default="sshleifer/tiny-gpt2", help="Small text model id to download for LoRA training.")
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
    download_model(args.feedback_model, FEEDBACK_BASE_DIR)
    print(f"Downloaded feedback base model to {FEEDBACK_BASE_DIR}")


if __name__ == "__main__":
    main()
