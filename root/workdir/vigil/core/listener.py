"""
VIGIL - Wake Word Listener
Always-on audio monitoring for wake word detection
"""

import time
import threading
import queue
from typing import Callable, Optional
import speech_recognition as sr

from config.settings import WAKE_WORDS, VoiceConfig, BOT_NAME


class WakeWordListener:
    """
    Continuously listens for wake words and triggers callback when detected.
    Uses speech_recognition with Google's free speech-to-text for wake word detection.
    """

    def __init__(self, on_wake: Callable[[str], None], on_error: Optional[Callable[[Exception], None]] = None):
        """
        Initialize the wake word listener.

        Args:
            on_wake: Callback function when wake word is detected. Receives the full phrase.
            on_error: Optional callback for error handling.
        """
        self.on_wake = on_wake
        self.on_error = on_error or self._default_error_handler
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone(sample_rate=VoiceConfig.SAMPLE_RATE)
        self.is_listening = False
        self._stop_event = threading.Event()
        self._listen_thread: Optional[threading.Thread] = None

        # Adjust for ambient noise on startup
        self._calibrate_microphone()

    def _calibrate_microphone(self):
        """Calibrate microphone for ambient noise."""
        print(f"[{BOT_NAME}] Calibrating microphone for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print(f"[{BOT_NAME}] Microphone calibrated. Ready to listen.")

    def _default_error_handler(self, error: Exception):
        """Default error handler."""
        print(f"[{BOT_NAME}] Listener error: {error}")

    def _normalize_text(self, text: str) -> str:
        """Normalize text for wake word comparison."""
        return text.lower().strip()

    def _contains_wake_word(self, text: str) -> bool:
        """Check if text contains any wake word."""
        normalized = self._normalize_text(text)
        for wake_word in WAKE_WORDS:
            if wake_word.lower() in normalized:
                return True
        return False

    def _extract_command(self, text: str) -> str:
        """Extract the command portion after the wake word."""
        normalized = self._normalize_text(text)

        # Find which wake word was used and extract what comes after
        for wake_word in sorted(WAKE_WORDS, key=len, reverse=True):
            wake_lower = wake_word.lower()
            if wake_lower in normalized:
                # Find position after wake word
                idx = normalized.find(wake_lower)
                command = text[idx + len(wake_word):].strip()
                # Clean up common trailing words
                for word in [",", ".", "?", "!"]:
                    command = command.strip(word)
                return command.strip()

        return text

    def _listen_loop(self):
        """Main listening loop running in background thread."""
        print(f"[{BOT_NAME}] Wake word listener active. Say one of: {', '.join(WAKE_WORDS)}")

        while not self._stop_event.is_set():
            try:
                with self.microphone as source:
                    # Listen for audio with timeout
                    audio = self.recognizer.listen(
                        source,
                        timeout=5,  # Max wait for speech to start
                        phrase_time_limit=10  # Max phrase length
                    )

                # Use Google's free speech recognition for wake word detection
                # This is lightweight and doesn't use API credits
                try:
                    text = self.recognizer.recognize_google(audio)
                    print(f"[{BOT_NAME}] Heard: '{text}'")

                    if self._contains_wake_word(text):
                        command = self._extract_command(text)
                        print(f"[{BOT_NAME}] Wake word detected! Command: '{command}'")
                        self.on_wake(text)

                except sr.UnknownValueError:
                    # Speech not understood - this is normal, continue listening
                    pass
                except sr.RequestError as e:
                    # Could not reach Google's service
                    self.on_error(Exception(f"Speech recognition service error: {e}"))
                    time.sleep(1)  # Brief pause before retry

            except sr.WaitTimeoutError:
                # No speech detected within timeout - this is normal
                pass
            except Exception as e:
                self.on_error(e)
                time.sleep(0.5)

    def start(self):
        """Start listening for wake words in background thread."""
        if self.is_listening:
            print(f"[{BOT_NAME}] Listener already running.")
            return

        self._stop_event.clear()
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()
        self.is_listening = True
        print(f"[{BOT_NAME}] Listener started.")

    def stop(self):
        """Stop the wake word listener."""
        if not self.is_listening:
            return

        self._stop_event.set()
        if self._listen_thread:
            self._listen_thread.join(timeout=3)
        self.is_listening = False
        print(f"[{BOT_NAME}] Listener stopped.")

    def restart(self):
        """Restart the listener (useful after errors)."""
        self.stop()
        time.sleep(0.5)
        self._calibrate_microphone()
        self.start()


class PushToTalkListener:
    """
    Alternative listener using push-to-talk (keyboard key).
    Useful for noisy environments or when wake word detection is unreliable.
    """

    def __init__(self, on_speech: Callable[[str], None], trigger_key: str = "space"):
        """
        Initialize push-to-talk listener.

        Args:
            on_speech: Callback when speech is captured.
            trigger_key: Key to hold for recording (default: space).
        """
        self.on_speech = on_speech
        self.trigger_key = trigger_key
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone(sample_rate=VoiceConfig.SAMPLE_RATE)
        self.is_active = False

    def record_once(self) -> Optional[str]:
        """Record a single phrase and return transcription."""
        print(f"[{BOT_NAME}] Listening...")

        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = self.recognizer.listen(source, phrase_time_limit=30)

        try:
            text = self.recognizer.recognize_google(audio)
            print(f"[{BOT_NAME}] You said: '{text}'")
            return text
        except sr.UnknownValueError:
            print(f"[{BOT_NAME}] Could not understand audio.")
            return None
        except sr.RequestError as e:
            print(f"[{BOT_NAME}] Recognition error: {e}")
            return None


if __name__ == "__main__":
    # Test the wake word listener
    def on_wake(phrase):
        print(f"\n🔔 WAKE WORD DETECTED: '{phrase}'\n")

    listener = WakeWordListener(on_wake=on_wake)
    listener.start()

    try:
        print("Listening for wake words... Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        listener.stop()
