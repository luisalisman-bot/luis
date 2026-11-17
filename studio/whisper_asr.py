"""Local multilingual Whisper for the portable Windows edition.

The bundled ONNX model exposes its alignment attention, so timestamps come
from the audio rather than distributing words evenly across a sentence.
One recognizer is shared under a lock to bound memory on a personal PC.
"""
import threading

import numpy as np

from . import config

_lock = threading.Lock()
_recognizer = None


def folder():
    return config.MODELS_DIR / "whisper-base"


def ready():
    return all((folder() / name).is_file() for name in (
        "base-encoder.int8.onnx", "base-decoder.int8.onnx", "base-tokens.txt"))


def ensure():
    if not ready():
        raise RuntimeError("Falta el modelo de voz. Extrae el ZIP completo de PeakCut y vuelve a abrirlo.")


def _get():
    global _recognizer
    if _recognizer is None:
        from .transcribe import _sherpa
        ensure()
        d = folder()
        _recognizer = _sherpa().OfflineRecognizer.from_whisper(
            encoder=str(d / "base-encoder.int8.onnx"),
            decoder=str(d / "base-decoder.int8.onnx"),
            tokens=str(d / "base-tokens.txt"),
            language=config.env("PEAKCUT_ASR_LANGUAGE", "es"),
            task="transcribe", provider="cpu",
            num_threads=max(1, min(4, int(config.env("PEAKCUT_ASR_THREADS", "4")))),
            enable_token_timestamps=True, enable_segment_timestamps=True)
    return _recognizer


def transcribe(audio, on_progress=None):
    from .transcribe import _chunks, _words
    chunks = list(_chunks(audio))
    out = []
    for i, (a, b) in enumerate(chunks):
        samples = audio[a:b].astype(np.float32) / 32768.0
        if len(samples) >= 4800 and float(np.sqrt(np.mean(samples ** 2))) >= 0.003:
            with _lock:
                recognizer = _get()
                stream = recognizer.create_stream()
                stream.accept_waveform(16000, samples)
                recognizer.decode_stream(stream)
                result = stream.result
                tokens, times = list(result.tokens), list(result.timestamps)
            if tokens and len(times) != len(tokens):
                raise RuntimeError("El modelo de voz no contiene la sincronizacion de palabras. Extrae el paquete completo.")
            words = _words(tokens, times, a, b)
            for j, w in enumerate(words):
                end = b / 16000.0
                if w["s"] >= end:
                    continue
                next_start = words[j + 1]["s"] if j + 1 < len(words) else end
                w["e"] = round(min(end, max(w["s"] + 0.02, min(next_start, max(w["e"], w["s"] + 0.4)))), 2)
                if out and out[-1]["s"] == w["s"] and out[-1]["w"] == w["w"]:
                    continue
                out.append(w)
        if on_progress:
            on_progress((i + 1) / max(1, len(chunks)))
    return out
