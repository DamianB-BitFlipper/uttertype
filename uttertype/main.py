from dotenv import load_dotenv
load_dotenv()  # Load environment variables up front

import asyncio
import os
from pynput import keyboard
from uttertype.transcribers import WhisperAPITranscriber, GeminiTranscriber, WhisperLocalMLXTranscriber
from uttertype.table_interface import ConsoleTable
from uttertype.key_listener import create_keylistener
from uttertype.utils import manual_type

async def main():
    # Choose transcriber based on environment variable
    transcriber_provider = os.getenv('UTTERTYPE_PROVIDER', 'openai').lower()
    
    if transcriber_provider == 'google':
        transcriber = GeminiTranscriber.create()
    elif transcriber_provider == 'openai':
        transcriber = WhisperAPITranscriber.create()
    elif transcriber_provider == 'mlx':
        transcriber = WhisperLocalMLXTranscriber.create()
    else:
        raise ValueError(f'Invalid transcriber provider: {transcriber_provider}')

    hotkey = create_keylistener(transcriber)

    keyboard_listener = keyboard.Listener(on_press=hotkey.press, on_release=hotkey.release)
    keyboard_listener.start()
    
    try:
        console_table = ConsoleTable()
        with console_table:
            async for transcription, audio_duration_ms in transcriber.get_transcriptions():
                manual_type(transcription)
                console_table.insert(
                    transcription,
                    round(0.0001 * audio_duration_ms / 1000, 6),
                )
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        pass
    finally:
        # Clean up resources
        keyboard_listener.stop()
        transcriber.cleanup()


def run_app():
    """Entry point for the uttertype application when installed via pip/uv"""
    asyncio.run(main())


if __name__ == "__main__":
    run_app()
