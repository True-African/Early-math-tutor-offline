from __future__ import annotations

import csv
import json
import math
import wave
from pathlib import Path

import numpy as np


try:
    from transformers import pipeline  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pipeline = None


ASR_PLAN = {
    "status": "optional_real_pipeline",
    "recommended_seed_models": ["openai/whisper-tiny", "facebook/mms-1b-all"],
    "safe_baseline": "tap-first interaction with optional microphone path",
    "todo": [
        "collect child-number-word utterances from approved public sources",
        "augment child-like speech with pitch and tempo perturbation",
        "fine-tune and benchmark on CPU before bundling",
    ],
}


def readiness_note() -> str:
    return "The microphone path is real and wired into the app. If a local ASR model is not available yet, the tutor falls back to tap or typed responses."


def _ensure_mono(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return audio.astype(np.float32)
    return audio.mean(axis=1).astype(np.float32)


def _normalize_audio(audio: np.ndarray) -> np.ndarray:
    audio = _ensure_mono(audio)
    peak = np.max(np.abs(audio)) if len(audio) else 0.0
    return audio if peak <= 0 else audio / peak


def _resample_linear(audio: np.ndarray, factor: float) -> np.ndarray:
    if len(audio) < 4 or factor <= 0:
        return audio
    new_length = max(8, int(len(audio) / factor))
    old_idx = np.linspace(0, len(audio) - 1, num=len(audio))
    new_idx = np.linspace(0, len(audio) - 1, num=new_length)
    return np.interp(new_idx, old_idx, audio).astype(np.float32)


def pitch_shift(audio: np.ndarray, semitones: float) -> np.ndarray:
    factor = 2 ** (semitones / 12.0)
    return _resample_linear(audio, factor)


def tempo_stretch(audio: np.ndarray, stretch: float) -> np.ndarray:
    return _resample_linear(audio, stretch)


def add_classroom_noise(audio: np.ndarray, noise_level: float = 0.015) -> np.ndarray:
    noise = np.random.normal(0, noise_level, size=len(audio)).astype(np.float32)
    mixed = audio + noise
    return _normalize_audio(mixed)


def save_wav(path: Path, sample_rate: int, audio: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    clipped = np.clip(audio, -1.0, 1.0)
    pcm = (clipped * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())


def augment_child_speech_manifest(seed_manifest: Path, output_manifest: Path, audio_root: Path) -> dict:
    # This expands a seed manifest into child-like audio variants using pitch, tempo, and noise changes.
    rows = []
    if not seed_manifest.exists():
        return {"status": "missing_seed_manifest", "rows": 0}
    with seed_manifest.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            audio_path = audio_root / row["audio_path"]
            if not audio_path.exists():
                continue
            with wave.open(str(audio_path), "rb") as wf:
                sr = wf.getframerate()
                data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32767.0
            variants = [
                ("pitch_plus_3", pitch_shift(data, 3)),
                ("pitch_plus_5", pitch_shift(data, 5)),
                ("tempo_090", tempo_stretch(data, 0.90)),
                ("tempo_110", tempo_stretch(data, 1.10)),
                ("noise_overlay", add_classroom_noise(data)),
            ]
            for suffix, variant in variants:
                out_path = audio_root / "augmented" / f"{Path(row['audio_path']).stem}_{suffix}.wav"
                save_wav(out_path, sr, variant)
                new_row = dict(row)
                new_row["audio_path"] = str(out_path.relative_to(audio_root))
                new_row["augmentation"] = suffix
                rows.append(new_row)
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    with output_manifest.open("w", encoding="utf-8", newline="") as f:
        fieldnames = sorted({key for row in rows for key in row.keys()}) if rows else ["utt_id", "audio_path", "transcript_en", "language", "correctness", "augmentation"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return {"status": "ok", "rows": len(rows), "output_manifest": str(output_manifest)}


class OfflineASRService:
    def __init__(self, model_path: str | None = None):
        self.model_path = model_path
        self._pipe = None
        self._load_error = None

    def available(self) -> bool:
        return pipeline is not None and bool(self.model_path)

    def load(self) -> bool:
        if self._pipe is not None:
            return True
        if not self.available():
            self._load_error = "transformers is not installed or no local ASR model path is configured."
            return False
        try:
            # A small local Whisper checkpoint keeps the app offline at inference time.
            self._pipe = pipeline(
                "automatic-speech-recognition",
                model=self.model_path,
                tokenizer=self.model_path,
                feature_extractor=self.model_path,
                device=-1,
            )
            return True
        except Exception as exc:  # pragma: no cover - optional dependency path
            self._load_error = str(exc)
            self._pipe = None
            return False

    def transcribe(self, audio_blob, preferred_language: str = "kin") -> dict:
        if audio_blob is None:
            return {"status": "no_audio", "text": "", "message": "No audio was recorded."}
        sample_rate, audio = audio_blob
        audio = _normalize_audio(np.asarray(audio))
        rms = float(np.sqrt(np.mean(np.square(audio)))) if len(audio) else 0.0
        if rms < 0.01:
            return {"status": "too_quiet", "text": "", "message": "The recording was too quiet. Please try again."}
        if self.load():
            try:
                result = self._pipe({"array": audio, "sampling_rate": sample_rate}, generate_kwargs={"language": preferred_language})
                text = (result.get("text") or "").strip()
                return {"status": "ok", "text": text, "message": "Transcribed with local offline ASR."}
            except Exception as exc:  # pragma: no cover - optional dependency path
                return {"status": "error", "text": "", "message": f"ASR failed: {exc}"}
        return {
            "status": "fallback_only",
            "text": "",
            "message": "Microphone audio was captured, but no local ASR model is installed yet. Use tap or typed answer, or place a local Whisper model under models/asr.",
        }

    def status(self) -> dict:
        if self.available():
            ready = self.load()
            if ready:
                return {"ready": True, "message": f"Local ASR model loaded from {self.model_path}."}
            return {"ready": False, "message": self._load_error or "Local ASR model path configured, but not yet loaded."}
        return {"ready": False, "message": self._load_error or "No local ASR model configured yet."}


def asr_status_snapshot(model_path: str | None) -> dict:
    service = OfflineASRService(model_path=model_path)
    status = service.status()
    return {
        "mode": "offline_microphone_pipeline",
        "ready": status["ready"],
        "message": status["message"],
        "plan": ASR_PLAN,
    }
