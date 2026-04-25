from __future__ import annotations

import json
from pathlib import Path


try:
    import torch  # type: ignore
    from peft import PeftModel  # type: ignore
    from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
    from transformers.utils import logging as transformers_logging  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    torch = None
    PeftModel = None
    AutoModelForCausalLM = None
    AutoTokenizer = None
    transformers_logging = None


def generate_instruction_examples(curriculum: list[dict]) -> list[dict]:
    # Each curriculum item becomes one small instruction-following example for the feedback model.
    rows = []
    for item in curriculum:
        answer = item["answer_int"]
        stem = item.get("stem_en") or item.get("stem_kin") or item.get("stem_fr") or ""
        rows.append(
            {
                "instruction": f"You are a gentle early-math tutor. Ask the learner: {stem}",
                "input": "",
                "output": f"The correct answer is {answer}. Praise the child briefly, then explain the answer in one simple sentence.",
                "skill": item["skill"],
                "answer_int": answer,
            }
        )
    return rows


def _low_quality_generation(text: str) -> bool:
    # The tiny local model can repeat itself, so we reject obviously poor generations.
    words = [word.strip(".,!?;:").lower() for word in text.split() if word.strip()]
    if len(words) < 4:
        return True
    unique_words = set(words)
    if len(unique_words) <= 2:
        return True
    most_common = max(words.count(word) for word in unique_words)
    return (most_common / max(len(words), 1)) > 0.45


class LoRALanguageHead:
    def __init__(self, base_model: str | None = None, adapter_path: str | None = None):
        self.base_model = base_model
        self.adapter_path = adapter_path
        self.model = None
        self.tokenizer = None
        self.load_error = None

    def available(self) -> bool:
        return all([self.base_model, self.adapter_path, torch, PeftModel, AutoModelForCausalLM, AutoTokenizer])

    def load(self) -> bool:
        if self.model is not None and self.tokenizer is not None:
            return True
        if not self.available():
            missing = []
            if not torch or not PeftModel or not AutoModelForCausalLM or not AutoTokenizer:
                missing.append("transformers, peft, or torch")
            if not self.base_model:
                missing.append("base model")
            if not self.adapter_path:
                missing.append("adapter path")
            self.load_error = "LoRA path is not ready yet: missing " + ", ".join(missing) + "."
            return False
        previous_verbosity = None
        try:
            base_model_path = str(self.base_model)
            local_only = Path(base_model_path).exists()
            self.tokenizer = AutoTokenizer.from_pretrained(base_model_path, local_files_only=local_only)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            if transformers_logging is not None:
                previous_verbosity = transformers_logging.get_verbosity()
                transformers_logging.set_verbosity_error()
            base = AutoModelForCausalLM.from_pretrained(base_model_path, local_files_only=local_only)
            self.model = PeftModel.from_pretrained(base, self.adapter_path)
            self.model.eval()
            return True
        except Exception as exc:  # pragma: no cover - optional dependency path
            self.load_error = str(exc)
            return False
        finally:
            if transformers_logging is not None and previous_verbosity is not None:
                transformers_logging.set_verbosity(previous_verbosity)

    def template_feedback(self, item: dict, correct: bool, language: str) -> str:
        # This fallback keeps the app stable even when the tiny local language model is weak.
        if language == "fr":
            return (
                f"Bravo. La réponse était {item['answer_int']}."
                if correct
                else f"Bon effort. La bonne réponse était {item['answer_int']}."
            )
        if language == "kin":
            return (
                f"Ni byiza. Igisubizo ni {item['answer_int']}."
                if correct
                else f"Wagerageje neza. Igisubizo nyacyo ni {item['answer_int']}."
            )
        return (
            f"Great job. The answer was {item['answer_int']}."
            if correct
            else f"Good try. The correct answer was {item['answer_int']}."
        )

    def generate_feedback(self, item: dict, correct: bool, language: str = "en") -> dict:
        if self.load():
            prompt = (
                f"You are a warm early-math tutor. Skill: {item['skill']}. "
                f"Question: {item.get('stem_en', '')}. Correct answer: {item['answer_int']}. "
                f"The child was {'correct' if correct else 'incorrect'}. "
                f"Reply in {language} using one short praise sentence and one short teaching sentence."
            )
            try:
                inputs = self.tokenizer(prompt, return_tensors="pt")
                prompt_length = inputs["input_ids"].shape[1]
                with torch.no_grad():
                    output = self.model.generate(
                        **inputs,
                        max_new_tokens=48,
                        do_sample=False,
                        pad_token_id=self.tokenizer.eos_token_id,
                    )
                generated = output[0][prompt_length:]
                text = self.tokenizer.decode(generated, skip_special_tokens=True).strip()
                if not text or _low_quality_generation(text):
                    return {
                        "mode": "template",
                        "text": self.template_feedback(item, correct, language),
                        "error": "low_quality_generation",
                    }
                return {"mode": "lora", "text": text}
            except Exception as exc:  # pragma: no cover
                return {"mode": "template", "text": self.template_feedback(item, correct, language), "error": str(exc)}
        return {"mode": "template", "text": self.template_feedback(item, correct, language), "error": self.load_error}

    def status(self) -> dict:
        ready = self.load()
        if ready:
            message = f"LoRA language head loaded from {self.adapter_path}."
        else:
            message = self.load_error or "LoRA language head not configured yet."
        return {
            "ready": ready,
            "message": message,
        }


def write_instruction_dataset(curriculum: list[dict], output_path: Path) -> int:
    rows = generate_instruction_examples(curriculum)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)
