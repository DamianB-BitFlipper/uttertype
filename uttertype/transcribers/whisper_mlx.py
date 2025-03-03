"""
Local Whisper MLX transcriber implementation.
"""

import os
import io
import tempfile
from uttertype.transcribers.base import AudioTranscriber


class WhisperLocalMLXTranscriber(AudioTranscriber):
    """
    Transcriber implementation using local Whisper MLX models.
    
    This transcriber uses Apple MLX framework for running Whisper models locally.
    """
    
    def __init__(self, model_type="distil-medium.en", *args, **kwargs):
        """
        Initialize WhisperLocalMLXTranscriber.
        
        Args:
            model_type: Model type/size to use
        """
        super().__init__(*args, **kwargs)
        try:
            from lightning_whisper_mlx import LightningWhisperMLX
            self.model = LightningWhisperMLX(model_type)
        except ImportError:
            raise ImportError(
                "lightning-whisper-mlx not found. Install with: uv sync --extra mlx"
            )
    
    @staticmethod
    def create(*args, **kwargs):
        """
        Factory method to create a WhisperLocalMLXTranscriber.
        
        Returns:
            WhisperLocalMLXTranscriber instance
        """
        model_type = os.getenv('MLX_MODEL_NAME', 'distil-medium.en')
        return WhisperLocalMLXTranscriber(model_type=model_type)

    def transcribe_audio(self, audio: io.BytesIO) -> str:
        """
        Transcribe audio using local Whisper MLX model.
        
        Args:
            audio: Audio data in BytesIO object
            
        Returns:
            Transcription as text
        """
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
                tmpfile.write(audio.getvalue())
                transcription = self.model.transcribe(tmpfile.name)["text"]
                os.unlink(tmpfile.name)
            return transcription
        except Exception as e:
            print(f"Encountered Error: {e}")
            return ""