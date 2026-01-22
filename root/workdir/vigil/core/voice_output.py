"""
VIGIL - Voice Output (Text-to-Speech)
Premium voice using ElevenLabs with Windows SAPI fallback
"""

import io
import tempfile
import threading
from typing import Optional
from pathlib import Path

from config.settings import ELEVENLABS_API_KEY, VoiceConfig, BOT_NAME


class VoiceOutput:
    """
    Handles text-to-speech conversion.
    Primary: ElevenLabs API (premium, natural voice)
    Fallback: Windows SAPI (free, offline)
    """

    def __init__(self):
        self.elevenlabs_available = bool(ELEVENLABS_API_KEY)
        self.pyttsx3_engine = None

        # Initialize ElevenLabs if available
        if self.elevenlabs_available:
            try:
                from elevenlabs import ElevenLabs
                self.elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
                print(f"[{BOT_NAME}] ElevenLabs voice initialized.")
            except ImportError:
                print(f"[{BOT_NAME}] ElevenLabs not installed. Using fallback.")
                self.elevenlabs_available = False
            except Exception as e:
                print(f"[{BOT_NAME}] ElevenLabs init error: {e}. Using fallback.")
                self.elevenlabs_available = False

        # Initialize fallback TTS
        self._init_fallback()

    def _init_fallback(self):
        """Initialize pyttsx3 as fallback TTS."""
        try:
            import pyttsx3
            self.pyttsx3_engine = pyttsx3.init()
            # Configure voice
            voices = self.pyttsx3_engine.getProperty('voices')
            # Try to find a male voice
            for voice in voices:
                if 'male' in voice.name.lower() or 'david' in voice.name.lower():
                    self.pyttsx3_engine.setProperty('voice', voice.id)
                    break
            self.pyttsx3_engine.setProperty('rate', 175)  # Speed
            self.pyttsx3_engine.setProperty('volume', 0.9)
            print(f"[{BOT_NAME}] Fallback TTS (pyttsx3) initialized.")
        except Exception as e:
            print(f"[{BOT_NAME}] Fallback TTS init error: {e}")
            self.pyttsx3_engine = None

    def speak_elevenlabs(self, text: str) -> bool:
        """
        Speak using ElevenLabs API.
        Returns True if successful.
        """
        if not self.elevenlabs_available:
            return False

        try:
            from elevenlabs import play, Voice, VoiceSettings

            # Generate audio
            audio = self.elevenlabs_client.text_to_speech.convert(
                text=text,
                voice_id=VoiceConfig.ELEVENLABS_VOICE_ID,
                model_id=VoiceConfig.ELEVENLABS_MODEL,
            )

            # Play the audio
            # Convert generator to bytes if needed
            if hasattr(audio, '__iter__') and not isinstance(audio, bytes):
                audio_bytes = b''.join(audio)
            else:
                audio_bytes = audio

            # Save to temp file and play
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name

            # Play using pygame or fallback
            self._play_audio_file(tmp_path)

            # Cleanup
            Path(tmp_path).unlink(missing_ok=True)

            return True

        except Exception as e:
            print(f"[{BOT_NAME}] ElevenLabs speak error: {e}")
            return False

    def _play_audio_file(self, file_path: str):
        """Play an audio file using available player."""
        try:
            # Try pygame first
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            pygame.mixer.quit()
        except ImportError:
            # Fallback to playsound
            try:
                from playsound import playsound
                playsound(file_path)
            except ImportError:
                # Last resort: Windows command
                import subprocess
                import sys
                if sys.platform == 'win32':
                    subprocess.run(
                        ['powershell', '-c', f'(New-Object Media.SoundPlayer "{file_path}").PlaySync()'],
                        capture_output=True
                    )

    def speak_pyttsx3(self, text: str) -> bool:
        """
        Speak using pyttsx3 (Windows SAPI).
        Returns True if successful.
        """
        if not self.pyttsx3_engine:
            return False

        try:
            self.pyttsx3_engine.say(text)
            self.pyttsx3_engine.runAndWait()
            return True
        except Exception as e:
            print(f"[{BOT_NAME}] pyttsx3 speak error: {e}")
            return False

    def speak(self, text: str, use_elevenlabs: bool = True) -> bool:
        """
        Speak the given text.

        Args:
            text: Text to speak
            use_elevenlabs: Whether to try ElevenLabs first

        Returns:
            True if speech was successful
        """
        if not text or not text.strip():
            return False

        print(f"[{BOT_NAME}] Speaking: '{text[:50]}...' " if len(text) > 50 else f"[{BOT_NAME}] Speaking: '{text}'")

        # Try ElevenLabs first
        if use_elevenlabs and self.elevenlabs_available:
            if self.speak_elevenlabs(text):
                return True
            print(f"[{BOT_NAME}] ElevenLabs failed, falling back to pyttsx3...")

        # Fallback to pyttsx3
        return self.speak_pyttsx3(text)

    def speak_async(self, text: str, use_elevenlabs: bool = True):
        """
        Speak in a background thread (non-blocking).
        """
        thread = threading.Thread(
            target=self.speak,
            args=(text, use_elevenlabs),
            daemon=True
        )
        thread.start()
        return thread

    def set_voice(self, voice_id: str):
        """Change the ElevenLabs voice ID."""
        VoiceConfig.ELEVENLABS_VOICE_ID = voice_id
        print(f"[{BOT_NAME}] Voice changed to: {voice_id}")

    def list_elevenlabs_voices(self) -> list:
        """List available ElevenLabs voices."""
        if not self.elevenlabs_available:
            return []

        try:
            voices = self.elevenlabs_client.voices.get_all()
            return [(v.voice_id, v.name) for v in voices.voices]
        except Exception as e:
            print(f"[{BOT_NAME}] Could not list voices: {e}")
            return []


if __name__ == "__main__":
    # Test voice output
    voice = VoiceOutput()

    test_text = "Hello Louis. I am Vigil, your watchful guardian. I am here to serve and protect."

    print("Testing voice output...")
    success = voice.speak(test_text)

    if success:
        print("✅ Voice output successful!")
    else:
        print("❌ Voice output failed.")
