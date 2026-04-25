from __future__ import annotations

import argparse
from pathlib import Path


try:
    from ctranslate2.converters import TransformersConverter  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    TransformersConverter = None


ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"
DEFAULT_SOURCE_DIR = MODELS_DIR / "asr"
DEFAULT_OUTPUT_DIR = MODELS_DIR / "asr_quantized"
CTRANSLATE2_RESERVED_FILES = {
    "config.json",
    "model.bin",
    "shared_vocabulary.txt",
    "vocabulary.json",
    "vocabulary.txt",
}
DEFAULT_COPY_FILES = (
    "tokenizer.json",
    "tokenizer_config.json",
    "preprocessor_config.json",
    "generation_config.json",
    "config.json",
    "normalizer.json",
    "special_tokens_map.json",
    "added_tokens.json",
    "vocab.json",
    "merges.txt",
)


def available_copy_files(source_dir: Path) -> list[str]:
    return [
        filename
        for filename in DEFAULT_COPY_FILES
        if filename not in CTRANSLATE2_RESERVED_FILES and (source_dir / filename).exists()
    ]


def convert_asr_model(
    source_dir: Path,
    output_dir: Path,
    quantization: str = "int8",
    force: bool = False,
) -> Path:
    if TransformersConverter is None:
        raise RuntimeError(
            "ctranslate2 is not installed. Install requirements-advanced.txt before converting the ASR model."
        )
    if not source_dir.exists():
        raise FileNotFoundError(f"Source ASR model directory does not exist: {source_dir}")

    copy_files = available_copy_files(source_dir)
    converter = TransformersConverter(
        str(source_dir),
        copy_files=copy_files,
        low_cpu_mem_usage=True,
    )
    converter.convert(str(output_dir), quantization=quantization, force=force)
    return output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a local Whisper ASR model to a quantized CTranslate2 edge model.")
    parser.add_argument("--source-model-dir", default=str(DEFAULT_SOURCE_DIR), help="Directory containing the source Hugging Face Whisper model.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for the quantized CTranslate2 model.")
    parser.add_argument(
        "--quantization",
        default="int8",
        choices=["int8", "int8_float32", "int8_float16", "int8_bfloat16", "int16", "float16", "float32"],
        help="CTranslate2 quantization scheme to save on disk.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite the output directory if it already exists.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_dir = Path(args.source_model_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    copy_files = available_copy_files(source_dir)
    saved_dir = convert_asr_model(source_dir, output_dir, quantization=args.quantization, force=args.force)
    print(f"Saved quantized ASR model to {saved_dir}")
    if copy_files:
        print("Copied support files: " + ", ".join(copy_files))


if __name__ == "__main__":
    main()
