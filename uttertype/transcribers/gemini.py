"""
Google Gemini API transcriber implementation.
"""

import os
import io
from typing import Optional
from textwrap import dedent
from pydantic import BaseModel
from google import genai
from google.genai import types
from uttertype.transcribers.base import AudioTranscriber


class GeminiTranscriber(AudioTranscriber):
    """
    Transcriber implementation using Google's Gemini API.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 use_vertex: bool = False,
                 project: Optional[str] = None, 
                 location: str = "us-central1",
                 model: str = "gemini-2.0-flash",
                 *args, **kwargs):
        """
        Initialize GeminiTranscriber.
        
        Args:
            api_key: Gemini API key
            use_vertex: Whether to use Vertex AI
            project: GCP project ID (required for Vertex AI)
            location: GCP region/location
            model: Gemini model name
        """
        super().__init__(*args, **kwargs)
        
        if use_vertex:
            if not project:
                raise ValueError("Project ID is required for Vertex AI")
            self.client = genai.Client(
                vertexai=True,
                project=project,
                location=location
            )
        else:
            if not api_key:
                raise ValueError("API key is required for Gemini API")
            self.client = genai.Client(api_key=api_key)
        
        self.model_name = model
        self.prompt = dedent("""\
        Audio Transcription Guidelines

        Your task is to transcribe the provided audio accurately. Whether the audio contains normal speech or technical content with varied speeds, please adhere to the following guidelines:

        1. Transcribe exactly what is spoken, preserving the original meaning and content.

        2. Assume English is spoken, unless it is clear another language is spoken.

        3. Numbers should be numerical and not written as words.

        4. For special characters that are spoken by name (such as "underscore," "dash," "period"), convert them to their corresponding symbols (_, -, .) when contextually appropriate, such as in:
          - Email addresses
          - Website URLs
          - File names
          - Programming code
          - Mathematical expressions

        5. Maintain proper punctuation, capitalization, and paragraph breaks to enhance readability.

        6. For technical content, preserve technical terms, acronyms, and specialized vocabulary exactly as spoken.

        7. Remove any ums and uhs. Connect their thought so that it is fluid.

        8. The user may have self-edited while speaking. If the user corrects themselves (usually via some interjection like "I meant" or "no, no"), edit the transcription to reflect their intended meaning rather than including the correction process itself.

        <EXAMPLE>
        User Said: "The art of doing science and engineering. I mean just science."
        Expected Transcription: "The art of doing science."
        </EXAMPLE>

        Note:
        Before transcribing the input audio, you have to make a determination if the audio contains any dictation audio. You may hear silence or music. In this case, set the `is_there_dictation` to False. If you hear a dictation, set this to `True` and transcribe the dictation.

        Below will follow the audio.
        """)

    @staticmethod
    def create(*args, **kwargs):
        """
        Factory method to create a GeminiTranscriber.
        
        Returns:
            GeminiTranscriber instance
        """
        use_vertex = os.getenv('GEMINI_USE_VERTEX', 'false').lower() in ('true', 'yes', '1', 't')
        project = os.getenv('GEMINI_PROJECT_ID')
        api_key = os.getenv('GEMINI_API_KEY')
        model = os.getenv('GEMINI_MODEL_NAME', 'gemini-2.0-flash')
        location = os.getenv('GEMINI_LOCATION', 'us-central1')
        
        return GeminiTranscriber(
            api_key=api_key,
            use_vertex=use_vertex,
            project=project,
            location=location,
            model=model
        )
    
    def transcribe_audio(self, audio: io.BytesIO) -> str:
        """
        Transcribe audio using Google Gemini API.
        
        Args:
            audio: Audio data in BytesIO object
            
        Returns:
            Transcription as text
        """
        try:
            # Get the audio bytes directly from the BytesIO object
            audio_bytes = audio.getvalue()

            class TranscriptionOut(BaseModel):
              is_there_dictation: bool
              transcription: str

            # Send to Gemini API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    self.prompt,
                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type='audio/wav',
                    ),
                ],
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': TranscriptionOut,
                },
            )

            # No dictation was detected, so return empty string
            if not response.parsed.is_there_dictation:
                return ""

            # Extract transcription from response
            transcription = response.parsed.transcription.strip()
            return transcription
            
        except Exception as e:
            print(f"Gemini Transcription Error: {e}")
            return ""