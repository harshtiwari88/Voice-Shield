"""
Transcript source for the risk_engine's context/action-risk indicators.

None of the uploaded files included a speech-to-text component, so
risk_engine.indicators (which scans a call TRANSCRIPT for phrases like
"transfer money" or "don't call me back") had nothing to run on.

This module defines a small interface so the team can plug in whichever
STT they end up using (Whisper API, Google Cloud STT, Vosk offline model,
etc.) without changing main.py. Until one is wired in, NullTranscriptionProvider
returns "" and the pipeline degrades gracefully: context_risk = 0 and
action_risk falls back to its no-indicators baseline (0.10), so the final
score is still computed, just from voice + reliability only.
"""

from __future__ import annotations
import numpy as np


class TranscriptionProvider:
    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        raise NotImplementedError


class NullTranscriptionProvider(TranscriptionProvider):
    """Placeholder used until a real STT backend is configured."""

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        return ""


# TODO (team): swap this for a real provider, e.g.:
#
# class WhisperTranscriptionProvider(TranscriptionProvider):
#     def __init__(self, model_size="base"):
#         import whisper
#         self.model = whisper.load_model(model_size)
#
#     def transcribe(self, audio, sample_rate):
#         result = self.model.transcribe(audio, fp16=False)
#         return result["text"]
#
# Then in main.py: transcription_provider = WhisperTranscriptionProvider()

transcription_provider: TranscriptionProvider = NullTranscriptionProvider()
