"""
Transcriber module for UtterType.

This module provides different transcriber implementations for speech-to-text.
"""

from uttertype.transcribers.base import AudioTranscriber
from uttertype.transcribers.whisper_api import WhisperAPITranscriber
from uttertype.transcribers.whisper_mlx import WhisperLocalMLXTranscriber
from uttertype.transcribers.gemini import GeminiTranscriber

__all__ = [
    'AudioTranscriber',
    'WhisperAPITranscriber',
    'WhisperLocalMLXTranscriber',
    'GeminiTranscriber',
]