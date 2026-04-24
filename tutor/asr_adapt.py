from __future__ import annotations

import csv
import json
import os
import wave
from pathlib import Path

import numpy as np


try:
    from faster_whisper import WhisperModel  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    WhisperModel = None

try:
    from transformers import pipeline  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pipeline = None


ASR_PLAN = {
    "status": "quantized_edge_ready",
    "recommended_seed_models": ["openai/whisper-tiny", "facebook/mms-1b-all"],
    "safe_baseline": "tap-first interaction with optional microphone path",
    "edge_path": "Convert Whisper to CTranslate2 int8 under models/asr_quantized and prefer faster-whisper on CPU edge devices.",
    "todo": [
        "collect child-number-word utterances from approved public sources",
        "augment child-like speech with pitch and tempo perturbation",
        "benchmark quantized ASR on target CPU and RAM budgets",
    ],
}

WHISPER_LANGUAGE_HINTS = {
    "en": "en",
    "fr": "fr",
}

QUANTIZED_MODEL_MARKERS = ("model.bin", "config.json")


def readiness_note() -> str:
    return (
        "The microphone path is real and wired into the app. "
        "If a quantized or standard local ASR model is not available yet, the tutor falls back to tap or typed responses."
    )


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


def _resample_for_whisper(audio: np.ndarray, sample_rate: int, target_rate: int = 16000) -> np.ndarray:
    audio = _normalize_audio(np.asarray(audio))
    if sample_rate <= 0 or sample_rate == target_rate:
        return audio
    factor = sample_rate / float(target_rate)
    return _normalize_audio(_resample_linear(audio, factor))


def _language_hint(preferred_language: str | None) -> str | None:
    return WHISPER_LANGUAGE_HINTS.get((preferred_language or "").strip().lower())


def _is_quantized_model_dir(model_path: str | None) -> bool:
    if not model_path:
        return False
    model_dir = Path(model_path)
    return model_dir.exists() and all((model_dir / marker).exists() for marker in QUANTIZED_MODEL_MARKERS)


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
        fieldnames = (
            sorted({key for row in rows for key in row.keys()})
            if rows
            else ["utt_id", "audio_path", "transcript_en", "language", "correctness", "augmentation"]
        )
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return {"status": "ok", "rows": len(rows), "output_manifest": str(output_manifest)}


class OfflineASRService:
    def __init__(
        self,
        model_path: str | None = None,
        quantized_model_path: str | None = None,
        device: str = "cpu",
        compute_type: str = "default",
    ):
        self.model_path = model_path
        self.quantized_model_path = quantized_model_path
        self.device = device
        self.compute_type = compute_type
        self._pipe = None
        self._quantized_model = None
        self._load_error = None
        self._backend = "none"

    def quantized_available(self) -> bool:
        return WhisperModel is not None and _is_quantized_model_dir(self.quantized_model_path)

    def standard_available(self) -> bool:
        return pipeline is not None and bool(self.model_path)

    def available(self) -> bool:
        return self.quantized_available() or self.standard_available()

    def availability_message(self) -> str:
        if _is_quantized_model_dir(self.quantized_model_path) and WhisperModel is None:
            return (
                "Quantized ASR files were found, but faster-whisper is not installed. "
                "Install requirements-advanced.txt to enable the edge int8 path."
            )
        if self.quantized_available():
            return f"Quantized local ASR is ready from {self.quantized_model_path}."
        if self.standard_available():
            return f"Standard local Whisper ASR is ready from {self.model_path}."
        if self.quantized_model_path and not _is_quantized_model_dir(self.quantized_model_path):
            return (
                "No quantized ASR model was found under the configured directory. "
                "Run python scripts/quantize_asr_model.py to prepare the int8 edge path."
            )
        if pipeline is None and WhisperModel is None and not self.model_path:
            return (
                "Speech-to-text is optional in this lightweight build. "
                "Use tap or typed answers, or install requirements-advanced.txt and add a local model under models/asr."
            )
        if pipeline is None and not self.quantized_available():
            return (
                "Speech-to-text dependencies are not installed in this lightweight build yet. "
                "Install requirements-advanced.txt to enable local transcription."
            )
        if not self.model_path:
            return (
                "No local speech-to-text model was found under models/asr. "
                "Use tap or typed answers, or place a local Whisper model there."
            )
        return "Local speech-to-text is ready to load."

    def _load_quantized(self) -> bool:
        if self._quantized_model is not None:
            return True
        if not self.quantized_available():
            return False
        try:
            cpu_threads = max(1, min(8, os.cpu_count() or 4))
            self._quantized_model = WhisperModel(
                self.quantized_model_path,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=cpu_threads,
            )
            self._backend = "faster_whisper"
            self._load_error = None
            return True
        except Exception as exc:  # pragma: no cover - optional dependency path
            self._load_error = f"Quantized ASR failed to load: {exc}"
            self._quantized_model = None
            return False

    def _load_standard(self) -> bool:
        if self._pipe is not None:
            return True
        if not self.standard_available():
            return False
        try:
            self._pipe = pipeline(
                "automatic-speech-recognition",
                model=self.model_path,
                tokenizer=self.model_path,
                feature_extractor=self.model_path,
                device=-1,
            )
            self._backend = "transformers"
            self._load_error = None
            return True
        except Exception as exc:  # pragma: no cover - optional dependency path
            self._load_error = str(exc)
            self._pipe = None
            return False

    def load(self) -> bool:
        if self._load_quantized():
            return True
        if self._load_standard():
            return True
        if not self._load_error:
            self._load_error = self.availability_message()
        return False

    def _transcribe_quantized(self, sample_rate: int, audio: np.ndarray, preferred_language: str) -> dict:
        if self._quantized_model is None:
            return {"status": "error", "text": "", "message": "Quantized ASR is not loaded."}
        whisper_audio = _resample_for_whisper(audio, sample_rate, target_rate=16000)
        language_hint = _language_hint(preferred_language)
        transcribe_kwargs = {
            "beam_size": 1,
            "best_of": 1,
            "condition_on_previous_text": False,
            "vad_filter": False,
            "temperature": 0.0,
        }
        if language_hint:
            transcribe_kwargs["language"] = language_hint
        try:
            segments, info = self._quantized_model.transcribe(whisper_audio, **transcribe_kwargs)
            text = " ".join(segment.text.strip() for segment in list(segments) if segment.text.strip()).strip()
            if not text:
                return {"status": "empty", "text": "", "message": "No speech was recognized from the recording."}
            language_name = getattr(info, "language", None) or "auto"
            return {
                "status": "ok",
                "text": text,
                "message": f"Transcribed with quantized local ASR ({language_name}).",
            }
        except Exception as exc:  # pragma: no cover - optional dependency path
            return {"status": "error", "text": "", "message": f"Quantized ASR failed: {exc}"}

    def _transcribe_standard(self, sample_rate: int, audio: np.ndarray, preferred_language: str) -> dict:
        if self._pipe is None:
            return {"status": "error", "text": "", "message": "Standard ASR is not loaded."}
        try:
            generate_kwargs = {}
            language_hint = _language_hint(preferred_language)
            if language_hint:
                generate_kwargs["language"] = language_hint
            audio_input = {"array": _normalize_audio(np.asarray(audio)), "sampling_rate": sample_rate}
            if generate_kwargs:
                result = self._pipe(audio_input, generate_kwargs=generate_kwargs)
            else:
                result = self._pipe(audio_input)
            text = (result.get("text") or "").strip()
            return {"status": "ok", "text": text, "message": "Transcribed with standard local offline ASR."}
        except Exception as exc:  # pragma: no cover - optional dependency path
            return {"status": "error", "text": "", "message": f"ASR failed: {exc}"}

    def transcribe(self, audio_blob, preferred_language: str = "kin") -> dict:
        if audio_blob is None:
            return {"status": "no_audio", "text": "", "message": "No audio was recorded."}
        sample_rate, audio = audio_blob
        audio = _normalize_audio(np.asarray(audio))
        rms = float(np.sqrt(np.mean(np.square(audio)))) if len(audio) else 0.0
        if rms < 0.01:
            return {"status": "too_quiet", "text": "", "message": "The recording was too quiet. Please try again."}
        if self.load():
            if self._quantized_model is not None:
                return self._transcribe_quantized(sample_rate, audio, preferred_language)
            if self._pipe is not None:
                return self._transcribe_standard(sample_rate, audio, preferred_language)
        return {
            "status": "fallback_only",
            "text": "",
            "message": "Microphone audio was captured. " + (self._load_error or self.availability_message()),
        }

    def status(self, load_model: bool = False) -> dict:
        if load_model:
            ready = self.load()
        else:
            ready = self.available()
        if self._quantized_model is not None:
            return {
                "ready": True,
                "backend": "faster_whisper",
                "message": f"Quantized local ASR loaded from {self.quantized_model_path}.",
            }
        if self._pipe is not None:
            return {
                "ready": True,
                "backend": "transformers",
                "message": f"Standard local ASR loaded from {self.model_path}.",
            }
        if self.quantized_available():
            return {
                "ready": ready,
                "backend": "faster_whisper",
                "message": f"Quantized local ASR is available at {self.quantized_model_path}.",
            }
        if self.standard_available():
            return {
                "ready": ready,
                "backend": "transformers",
                "message": f"Standard local ASR is available at {self.model_path}.",
            }
        return {
            "ready": False,
            "backend": "none",
            "message": self._load_error or self.availability_message(),
        }


def asr_status_snapshot(
    model_path: str | None,
    quantized_model_path: str | None = None,
    load_model: bool = False,
) -> dict:
    service = OfflineASRService(model_path=model_path, quantized_model_path=quantized_model_path)
    status = service.status(load_model=load_model)
    return {
        "mode": "offline_microphone_pipeline",
        "ready": status["ready"],
        "backend": status["backend"],
        "message": status["message"],
        "plan": ASR_PLAN,
    }
