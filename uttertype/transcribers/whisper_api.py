"""
OpenAI Whisper API transcriber implementation.
"""

import os
import io
from openai import OpenAI
from uttertype.transcribers.base import AudioTranscriber


class WhisperAPITranscriber(AudioTranscriber):
    """
    Transcriber implementation using OpenAI's Whisper API.
    """
    
    def __init__(self, base_url, model_name, *args, **kwargs):
        """
        Initialize WhisperAPITranscriber.
        
        Args:
            base_url: OpenAI API base URL
            model_name: Whisper model name
        """
        super().__init__(*args, **kwargs)

        self.model_name = model_name
        self.client = OpenAI(base_url=base_url)

    @staticmethod
    def create(*args, **kwargs):
        """
        Factory method to create a WhisperAPITranscriber.
        
        Returns:
            WhisperAPITranscriber instance
        """
        base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        model_name = os.getenv('OPENAI_MODEL_NAME', 'whisper-1')

        return WhisperAPITranscriber(base_url, model_name)

    def transcribe_audio(self, audio: io.BytesIO) -> str:
        """
        Transcribe audio using OpenAI Whisper API.
        
        Args:
            audio: Audio data in BytesIO object
            
        Returns:
            Transcription as text
        """
        try:
            transcription = self.client.audio.transcriptions.create(
                model=self.model_name,
                file=audio,
                response_format="text",
                language="en",
                prompt="The following is normal speech or technical speech from an engineer.",
            )
            return transcription
        except Exception as e:
            print(f"Encountered Error: {e}")
            return ""