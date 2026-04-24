from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tutor.curriculum_loader import load_curriculum
from tutor.lora_language import write_instruction_dataset

try:
    from datasets import load_dataset  # type: ignore
    from peft import LoraConfig, get_peft_model  # type: ignore
    from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, default_data_collator  # type: ignore
except Exception as exc:  # pragma: no cover
    load_dataset = None
    LoraConfig = None
    get_peft_model = None
    AutoModelForCausalLM = None
    AutoTokenizer = None
    Trainer = None
    TrainingArguments = None
    default_data_collator = None
    IMPORT_ERROR = str(exc)
else:
    IMPORT_ERROR = None


DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models" / "lora_numeracy_adapter"
BASE_MODEL_DIR = ROOT / "models" / "feedback_base"
INSTRUCTION_PATH = DATA_DIR / "numeracy_instructions.jsonl"
DATASET_CACHE_DIR = ROOT / ".cache" / "hf_datasets"


def prepare_dataset() -> int:
    curriculum = load_curriculum(DATA_DIR)
    return write_instruction_dataset(curriculum, INSTRUCTION_PATH)


def detect_target_modules(model) -> list[str]:
    names = {name.split(".")[-1] for name, _ in model.named_modules()}
    preferred = ["q_proj", "k_proj", "v_proj", "o_proj", "c_attn", "c_proj", "c_fc"]
    matches = [name for name in preferred if name in names]
    return matches or ["c_attn"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a tiny LoRA feedback adapter for the offline tutor.")
    parser.add_argument(
        "--base-model",
        default=str(BASE_MODEL_DIR) if BASE_MODEL_DIR.exists() else "sshleifer/tiny-gpt2",
        help="Local model path or Hugging Face model id to use as the LoRA base.",
    )
    parser.add_argument("--output-dir", default=str(MODEL_DIR), help="Directory to save the adapter.")
    parser.add_argument("--epochs", type=float, default=2.0, help="Number of training epochs.")
    parser.add_argument("--max-length", type=int, default=192, help="Token length for each training example.")
    return parser.parse_args()


def main() -> None:
    cli_args = parse_args()
    count = prepare_dataset()
    print(f"Wrote {count} instruction examples to {INSTRUCTION_PATH}")
    if IMPORT_ERROR:
        print("Advanced LoRA training dependencies are not installed.")
        print(f"Import error: {IMPORT_ERROR}")
        print("Install requirements-advanced.txt before running actual training.")
        return

    model_name = cli_args.base_model
    output_dir = Path(cli_args.output_dir)
    dataset = load_dataset("json", data_files=str(INSTRUCTION_PATH), cache_dir=str(DATASET_CACHE_DIR))["train"]
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    def format_row(row):
        text = f"### Instruction\n{row['instruction']}\n\n### Response\n{row['output']}"
        tokenized = tokenizer(text, truncation=True, padding="max_length", max_length=cli_args.max_length)
        tokenized["labels"] = tokenized["input_ids"].copy()
        return tokenized

    dataset = dataset.map(format_row, remove_columns=dataset.column_names)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    model.config.use_cache = False
    target_modules = detect_target_modules(model)
    fan_in_fan_out = any(name.startswith("c_") for name in target_modules)
    peft_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=target_modules,
        fan_in_fan_out=fan_in_fan_out,
    )
    model = get_peft_model(model, peft_config)
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        num_train_epochs=cli_args.epochs,
        logging_steps=5,
        save_strategy="epoch",
        save_total_limit=1,
        learning_rate=2e-4,
        report_to=[],
        remove_unused_columns=False,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=default_data_collator,
    )
    trainer.train()
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    metadata = {"base_model": model_name, "adapter_path": str(output_dir), "target_modules": target_modules}
    (output_dir / "adapter_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Saved LoRA adapter to {output_dir}")


if __name__ == "__main__":
    main()
