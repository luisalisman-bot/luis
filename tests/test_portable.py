"""Checks for the portable edition's language and model behavior."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from studio import brain, config, fetch_model, transcribe, whisper_asr


class PortableTests(unittest.TestCase):
    def test_spanish_is_not_translated_even_when_ai_is_available(self):
        words = [{"w": "increíble", "s": 0, "e": 0.8}, {"w": "niño", "s": 0.9, "e": 1.4},
                 {"w": "mañana", "s": 1.5, "e": 2}]
        with patch.dict(os.environ, {"PEAKCUT_CAPTION_LANGUAGE": "original"}), \
                patch.object(brain, "_fix_caption_words", return_value=words), \
                patch.object(brain, "translate_caption_words", side_effect=AssertionError("unexpected translation")):
            got = brain.english_captions(words, "es", youtube_english=lambda: self.fail("used English subtitles"))
        self.assertEqual(got, words)

    def test_silence_does_not_invent_words_or_load_model(self):
        progress = []
        with patch.object(whisper_asr, "_get", side_effect=AssertionError("loaded model for silence")):
            self.assertEqual(whisper_asr.transcribe(np.zeros(16000, dtype=np.int16), progress.append), [])
        self.assertEqual(progress[-1], 1)

    def test_model_readiness_requires_all_parts_and_never_downloads_parakeet(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(whisper_asr, "folder", return_value=Path(tmp)), \
                patch.dict(os.environ, {"PEAKCUT_ASR_BACKEND": "whisper"}), \
                patch("urllib.request.urlretrieve", side_effect=AssertionError("unexpected download")):
            self.assertFalse(fetch_model.ready())
            with self.assertRaises(RuntimeError):
                fetch_model.ensure()
            for name in ("base-encoder.int8.onnx", "base-decoder.int8.onnx", "base-tokens.txt"):
                (Path(tmp) / name).write_bytes(b"test")
            self.assertTrue(fetch_model.ready())
            fetch_model.ensure()

    def test_accents_and_subword_tokens_keep_their_timing(self):
        got = transcribe._words([" incre", "íble", ".", " niño"], [0.2, 0.4, 0.7, 1.0], 16000, 48000)
        self.assertEqual([w["w"] for w in got], ["increíble.", "niño"])
        self.assertEqual([w["s"] for w in got], [1.2, 2.0])
        self.assertTrue(all(w["e"] > w["s"] for w in got))

    def test_whisper_dispatch_does_not_run_english_recognizer(self):
        with patch.dict(os.environ, {"PEAKCUT_ASR_BACKEND": "whisper"}), \
                patch.object(whisper_asr, "transcribe", return_value=[{"w": "hola"}]) as mocked, \
                patch.object(transcribe, "_take", side_effect=AssertionError("English recognizer used")):
            self.assertEqual(transcribe.transcribe(np.ones(16000, dtype=np.int16)), [{"w": "hola"}])
            mocked.assert_called_once()


if __name__ == "__main__":
    unittest.main()
