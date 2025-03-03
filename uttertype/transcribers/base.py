"""
Base transcriber implementation.
"""

import os
import io
from typing import List, Tuple
import pyaudio
import wave
import asyncio
from threading import Thread, Event
import webrtcvad
from uttertype.utils import transcription_concat

# Audio configuration constants
FORMAT = pyaudio.paInt16  # Audio format
CHANNELS = 1  # Mono audio
RATE = 16000  # Sample rate
CHUNK_DURATION_MS = 30  # Frame duration in milliseconds
CHUNK = int(RATE * CHUNK_DURATION_MS / 1000)
# Minimum duration of speech to send to API as a chunk between gaps of silence
MIN_TRANSCRIPTION_CHUNK_SIZE_MS = 10000
# Minimum duration of recording to process (in milliseconds)
# Recordings shorter than this will be ignored (useful for preventing
# accidental transcriptions from quick hotkey presses)
MIN_RECORDING_DURATION_MS = int(os.getenv('UTTERTYPE_MIN_RECORDING_MS', 300))


class AudioTranscriber:
    """
    Base class for audio transcription implementations.
    
    This class handles the recording and preprocessing of audio data.
    Subclasses must implement the transcribe_audio method.
    """
    
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.recording_finished = Event()  # Threading event to end recording
        self.recording_finished.set()  # Initialize as finished
        self.frames = []
        self.audio_duration = 0
        self.rolling_transcriptions: List[Tuple[int, str]] = []  # (idx, transcription)
        self.rolling_requests: List[Thread] = []  # list of pending requests
        self.event_loop = asyncio.get_event_loop()
        self.vad = webrtcvad.Vad(1)  # Voice Activity Detector, mode can be 0 to 3
        self.transcriptions = asyncio.Queue()
        self.recording_canceled = False  # Flag to track if recording should be canceled
        self.stream = None  # Initialize stream as None until needed

    def start_recording(self):
        """Start recording audio from the microphone."""
        # Reset the canceled flag when starting a new recording
        self.recording_canceled = False
        
        # Start a new recording in the background, do not block
        def _record():
            self.recording_finished = Event()
            # Create audio stream only when recording starts
            self.stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
            )
            intermediate_trancriptions_idx = 0
            while (
                not self.recording_finished.is_set()
            ):  # Keep recording until interrupted
                data = self.stream.read(CHUNK)
                self.audio_duration += CHUNK_DURATION_MS
                is_speech = self.vad.is_speech(data, RATE)
                current_audio_duration = len(self.frames) * CHUNK_DURATION_MS
                if (
                    not is_speech
                    and current_audio_duration >= MIN_TRANSCRIPTION_CHUNK_SIZE_MS
                ):  # silence
                    rolling_request = Thread(
                        target=self._intermediate_transcription,
                        args=(
                            intermediate_trancriptions_idx,
                            self._frames_to_wav(),
                        ),
                    )
                    self.frames = []
                    self.rolling_requests.append(rolling_request)
                    rolling_request.start()
                    intermediate_trancriptions_idx += 1
                self.frames.append(data)
            
            # Close audio stream after recording is finished
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None

        # start recording in a new non-blocking thread
        Thread(target=_record).start()

    def stop_recording(self):
        """Stop the recording and reset variables"""
        self.recording_finished.set()
        
        # Skip processing if recording is too short or was canceled
        if self.audio_duration < MIN_RECORDING_DURATION_MS or self.recording_canceled:
            # Reset variables without processing
            self.frames = []
            self.audio_duration = 0
            self.rolling_requests = []
            self.rolling_transcriptions = []
            # Reset canceled flag
            self.recording_canceled = False
            return
            
        self._finish_transcription()
        self.frames = []
        self.audio_duration = 0
        self.rolling_requests = []
        self.rolling_transcriptions = []
        # Reset canceled flag
        self.recording_canceled = False

    def _intermediate_transcription(self, idx, audio):
        intermediate_transcription = self.transcribe_audio(audio)
        self.rolling_transcriptions.append((idx, intermediate_transcription))

    def _finish_transcription(self):
        for request in self.rolling_requests:  # Wait for all of the rolling requests
            request.join()

        # Process the final transcription chunk
        final_transcription_chunk = self.transcribe_audio(
            self._frames_to_wav()
        )

        # Sort by idx
        sorted_transcription_chunks = sorted(self.rolling_transcriptions, key=lambda x: x[0])

        # Get only the transcription texts
        transcriptions = [t[1] for t in sorted_transcription_chunks] + [final_transcription_chunk]

        # Put final combined result in finished queue
        self.event_loop.call_soon_threadsafe(
            self.transcriptions.put_nowait,
            (transcription_concat(transcriptions), self.audio_duration),
        )

    def _frames_to_wav(self):
        buffer = io.BytesIO()
        buffer.name = "tmp.wav"
        wf = wave.open(buffer, "wb")
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(self.frames))
        wf.close()
        return buffer
        
    def cancel_recording(self):
        """Mark the current recording as canceled so it will not be processed"""
        self.recording_canceled = True

    def transcribe_audio(self, audio: io.BytesIO) -> str:
        """
        Transcribe audio data to text.
        
        Args:
            audio: Audio data in BytesIO object.
            
        Returns:
            Transcription as text.
        """
        raise NotImplementedError("Please use a subclass of AudioTranscriber")

    async def get_transcriptions(self):
        """
        Asynchronously get transcriptions from the queue.
        Returns (transcription string, audio duration in ms).
        """
        while True:
            transcription = await self.transcriptions.get()
            yield transcription
            self.transcriptions.task_done()
            
    def cleanup(self):
        """Clean up resources when shutting down."""
        # Close the audio stream if it's open
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            
        # Terminate PyAudio instance
        if hasattr(self, 'audio') and self.audio:
            self.audio.terminate()