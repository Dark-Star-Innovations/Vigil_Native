+   1 """
+   2 VIGIL - Wake Word Listener
+   3 Always-on audio monitoring for wake word detection
+   4 """
+   5 
+   6 import time
+   7 import threading
+   8 import queue
+   9 from typing import Callable, Optional
+  10 import speech_recognition as sr
+  11 
+  12 from config.settings import WAKE_WORDS, VoiceConfig, BOT_NAME
+  13 
+  14 
+  15 class WakeWordListener:
+  16     """
+  17     Continuously listens for wake words and triggers callback when detected.
+  18     Uses speech_recognition with Google's free speech-to-text for wake word detection.
+  19     """
+  20 
+  21     def __init__(self, on_wake: Callable[[str], None], on_error: Optional[Callable[[Exception], None]] = None):
+  22         """
+  23         Initialize the wake word listener.
+  24 
+  25         Args:
+  26             on_wake: Callback function when wake word is detected. Receives the full phrase.
+  27             on_error: Optional callback for error handling.
+  28         """
+  29         self.on_wake = on_wake
+  30         self.on_error = on_error or self._default_error_handler
+  31         self.recognizer = sr.Recognizer()
+  32         self.microphone = sr.Microphone(sample_rate=VoiceConfig.SAMPLE_RATE)
+  33         self.is_listening = False
+  34         self._stop_event = threading.Event()
+  35         self._listen_thread: Optional[threading.Thread] = None
+  36 
+  37         # Adjust for ambient noise on startup
+  38         self._calibrate_microphone()
+  39 
+  40     def _calibrate_microphone(self):
+  41         """Calibrate microphone for ambient noise."""
+  42         print(f"[{BOT_NAME}] Calibrating microphone for ambient noise...")
+  43         with self.microphone as source:
+  44             self.recognizer.adjust_for_ambient_noise(source, duration=2)
+  45         print(f"[{BOT_NAME}] Microphone calibrated. Ready to listen.")
+  46 
+  47     def _default_error_handler(self, error: Exception):
+  48         """Default error handler."""
+  49         print(f"[{BOT_NAME}] Listener error: {error}")
+  50 
+  51     def _normalize_text(self, text: str) -> str:
+  52         """Normalize text for wake word comparison."""
+  53         return text.lower().strip()
+  54 
+  55     def _contains_wake_word(self, text: str) -> bool:
+  56         """Check if text contains any wake word."""
+  57         normalized = self._normalize_text(text)
+  58         for wake_word in WAKE_WORDS:
+  59             if wake_word.lower() in normalized:
+  60                 return True
+  61         return False
+  62 
+  63     def _extract_command(self, text: str) -> str:
+  64         """Extract the command portion after the wake word."""
+  65         normalized = self._normalize_text(text)
+  66 
+  67         # Find which wake word was used and extract what comes after
+  68         for wake_word in sorted(WAKE_WORDS, key=len, reverse=True):
+  69             wake_lower = wake_word.lower()
+  70             if wake_lower in normalized:
+  71                 # Find position after wake word
+  72                 idx = normalized.find(wake_lower)
+  73                 command = text[idx + len(wake_word):].strip()
+  74                 # Clean up common trailing words
+  75                 for word in [",", ".", "?", "!"]:
+  76                     command = command.strip(word)
+  77                 return command.strip()
+  78 
+  79         return text
+  80 
+  81     def _listen_loop(self):
+  82         """Main listening loop running in background thread."""
+  83         print(f"[{BOT_NAME}] Wake word listener active. Say one of: {', '.join(WAKE_WORDS)}")
+  84 
+  85         while not self._stop_event.is_set():
+  86             try:
+  87                 with self.microphone as source:
+  88                     # Listen for audio with timeout
+  89                     audio = self.recognizer.listen(
+  90                         source,
+  91                         timeout=5,  # Max wait for speech to start
+  92                         phrase_time_limit=10  # Max phrase length
+  93                     )
+  94 
+  95                 # Use Google's free speech recognition for wake word detection
+  96                 # This is lightweight and doesn't use API credits
+  97                 try:
+  98                     text = self.recognizer.recognize_google(audio)
+  99                     print(f"[{BOT_NAME}] Heard: '{text}'")
+ 100 
+ 101                     if self._contains_wake_word(text):
+ 102                         command = self._extract_command(text)
+ 103                         print(f"[{BOT_NAME}] Wake word detected! Command: '{command}'")
+ 104                         self.on_wake(text)
+ 105 
+ 106                 except sr.UnknownValueError:
+ 107                     # Speech not understood - this is normal, continue listening
+ 108                     pass
+ 109                 except sr.RequestError as e:
+ 110                     # Could not reach Google's service
+ 111                     self.on_error(Exception(f"Speech recognition service error: {e}"))
+ 112                     time.sleep(1)  # Brief pause before retry
+ 113 
+ 114             except sr.WaitTimeoutError:
+ 115                 # No speech detected within timeout - this is normal
+ 116                 pass
+ 117             except Exception as e:
+ 118                 self.on_error(e)
+ 119                 time.sleep(0.5)
+ 120 
+ 121     def start(self):
+ 122         """Start listening for wake words in background thread."""
+ 123         if self.is_listening:
+ 124             print(f"[{BOT_NAME}] Listener already running.")
+ 125             return
+ 126 
+ 127         self._stop_event.clear()
+ 128         self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
+ 129         self._listen_thread.start()
+ 130         self.is_listening = True
+ 131         print(f"[{BOT_NAME}] Listener started.")
+ 132 
+ 133     def stop(self):
+ 134         """Stop the wake word listener."""
+ 135         if not self.is_listening:
+ 136             return
+ 137 
+ 138         self._stop_event.set()
+ 139         if self._listen_thread:
+ 140             self._listen_thread.join(timeout=3)
+ 141         self.is_listening = False
+ 142         print(f"[{BOT_NAME}] Listener stopped.")
+ 143 
+ 144     def restart(self):
+ 145         """Restart the listener (useful after errors)."""
+ 146         self.stop()
+ 147         time.sleep(0.5)
+ 148         self._calibrate_microphone()
+ 149         self.start()
+ 150 
+ 151 
+ 152 class PushToTalkListener:
+ 153     """
+ 154     Alternative listener using push-to-talk (keyboard key).
+ 155     Useful for noisy environments or when wake word detection is unreliable.
+ 156     """
+ 157 
+ 158     def __init__(self, on_speech: Callable[[str], None], trigger_key: str = "space"):
+ 159         """
+ 160         Initialize push-to-talk listener.
+ 161 
+ 162         Args:
+ 163             on_speech: Callback when speech is captured.
+ 164             trigger_key: Key to hold for recording (default: space).
+ 165         """
+ 166         self.on_speech = on_speech
+ 167         self.trigger_key = trigger_key
+ 168         self.recognizer = sr.Recognizer()
+ 169         self.microphone = sr.Microphone(sample_rate=VoiceConfig.SAMPLE_RATE)
+ 170         self.is_active = False
+ 171 
+ 172     def record_once(self) -> Optional[str]:
+ 173         """Record a single phrase and return transcription."""
+ 174         print(f"[{BOT_NAME}] Listening...")
+ 175 
+ 176         with self.microphone as source:
+ 177             self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
+ 178             audio = self.recognizer.listen(source, phrase_time_limit=30)
+ 179 
+ 180         try:
+ 181             text = self.recognizer.recognize_google(audio)
+ 182             print(f"[{BOT_NAME}] You said: '{text}'")
+ 183             return text
+ 184         except sr.UnknownValueError:
+ 185             print(f"[{BOT_NAME}] Could not understand audio.")
+ 186             return None
+ 187         except sr.RequestError as e:
+ 188             print(f"[{BOT_NAME}] Recognition error: {e}")
+ 189             return None
+ 190 
+ 191 
+ 192 if __name__ == "__main__":
+ 193     # Test the wake word listener
+ 194     def on_wake(phrase):
+ 195         print(f"\n🔔 WAKE WORD DETECTED: '{phrase}'\n")
+ 196 
+ 197     listener = WakeWordListener(on_wake=on_wake)
+ 198     listener.start()
+ 199 
+ 200     try:
+ 201         print("Listening for wake words... Press Ctrl+C to stop.")
+ 202         while True:
+ 203             time.sleep(1)
+ 204     except KeyboardInterrupt:
+ 205         print("\nStopping...")
+ 206         listener.stop()
