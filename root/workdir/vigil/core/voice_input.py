"""
VIGIL - Voice Input (Speech-to-Text)
High-quality transcription using OpenAI Whisper
"""

import io
import tempfile
import wave
from typing import Optional
from pathlib import Path

import speech_recognition as sr
from openai import OpenAI

from config.settings import OPENAI_API_KEY, VoiceConfig, BOT_NAME


class VoiceInput:
    """
    Handles speech-to-text conversion using OpenAI's Whisper API.
    Falls back to Google's free speech recognition if Whisper fails.
    """

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone(sample_rate=VoiceConfig.SAMPLE_RATE)
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

        # Calibrate on init
        self._calibrate()

    def _calibrate(self):
        """Adjust for ambient noise."""
        print(f"[{BOT_NAME}] Calibrating voice input...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def _audio_to_wav_bytes(self, audio: sr.AudioData) -> bytes:
        """Convert SpeechRecognition AudioData to WAV bytes."""
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(audio.sample_width)
            wav_file.setframerate(audio.sample_rate)
            wav_file.writeframes(audio.get_raw_data())
        wav_io.seek(0)
        return wav_io.read()

    def transcribe_with_whisper(self, audio: sr.AudioData) -> Optional[str]:
        """
        Transcribe audio using OpenAI's Whisper API.
        Returns None if transcription fails.
        """
        if not self.openai_client:
            return None

        try:
            # Convert audio to WAV format
            wav_bytes = self._audio_to_wav_bytes(audio)

            # Create a temporary file for the API
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(wav_bytes)
                tmp_path = tmp_file.name

            # Transcribe with Whisper
            with open(tmp_path, "rb") as audio_file:
                response = self.openai_client.audio.transcriptions.create(
                    model=VoiceConfig.WHISPER_MODEL,
                    file=audio_file,
                    response_format="text"
                )

            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)

            return response.strip() if response else None

        except Exception as e:
            print(f"[{BOT_NAME}] Whisper transcription error: {e}")
            return None

    def transcribe_with_google(self, audio: sr.AudioData) -> Optional[str]:
        """
        Transcribe audio using Google's free speech recognition.
        Fallback option.
        """
        try:
            text = self.recognizer.recognize_google(audio)
            return text.strip() if text else None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"[{BOT_NAME}] Google recognition error: {e}")
            return None

    def listen_and_transcribe(self, timeout: int = 10, phrase_limit: int = 30) -> Optional[str]:
        """
        Listen for speech and transcribe it.

        Args:
            timeout: Max seconds to wait for speech to begin
            phrase_limit: Max seconds for the phrase

        Returns:
            Transcribed text or None if failed
        """
        try:
            with self.microphone as source:
                print(f"[{BOT_NAME}] Listening...")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_limit
                )

            # Try Whisper first (higher quality)
            text = self.transcribe_with_whisper(audio)

            # Fall back to Google if Whisper fails
            if text is None:
                print(f"[{BOT_NAME}] Falling back to Google transcription...")
                text = self.transcribe_with_google(audio)

            if text:
                print(f"[{BOT_NAME}] Transcribed: '{text}'")

            return text

        except sr.WaitTimeoutError:
            print(f"[{BOT_NAME}] No speech detected (timeout)")
            return None
        except Exception as e:
            print(f"[{BOT_NAME}] Listen error: {e}")
            return None

    def transcribe_file(self, audio_path: str) -> Optional[str]:
        """
        Transcribe an audio file.

        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)

        Returns:
            Transcribed text or None
        """
        if not self.openai_client:
            print(f"[{BOT_NAME}] OpenAI client not available for file transcription")
            return None

        try:
            with open(audio_path, "rb") as audio_file:
                response = self.openai_client.audio.transcriptions.create(
                    model=VoiceConfig.WHISPER_MODEL,
                    file=audio_file,
                    response_format="text"
                )
            return response.strip() if response else None

        except Exception as e:
            print(f"[{BOT_NAME}] File transcription error: {e}")
            return None


if __name__ == "__main__":
    # Test voice input
    voice_input = VoiceInput()

    print("Say something...")
    text = voice_input.listen_and_transcribe()

    if text:
        print(f"\n✅ You said: '{text}'")
    else:
        print("\n❌ Could not transcribe speech")
