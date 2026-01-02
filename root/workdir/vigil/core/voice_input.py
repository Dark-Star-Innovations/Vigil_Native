+   1 """
+   2 VIGIL - Voice Input (Speech-to-Text)
+   3 High-quality transcription using OpenAI Whisper
+   4 """
+   5 
+   6 import io
+   7 import tempfile
+   8 import wave
+   9 from typing import Optional
+  10 from pathlib import Path
+  11 
+  12 import speech_recognition as sr
+  13 from openai import OpenAI
+  14 
+  15 from config.settings import OPENAI_API_KEY, VoiceConfig, BOT_NAME
+  16 
+  17 
+  18 class VoiceInput:
+  19     """
+  20     Handles speech-to-text conversion using OpenAI's Whisper API.
+  21     Falls back to Google's free speech recognition if Whisper fails.
+  22     """
+  23 
+  24     def __init__(self):
+  25         self.recognizer = sr.Recognizer()
+  26         self.microphone = sr.Microphone(sample_rate=VoiceConfig.SAMPLE_RATE)
+  27         self.openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
+  28 
+  29         # Calibrate on init
+  30         self._calibrate()
+  31 
+  32     def _calibrate(self):
+  33         """Adjust for ambient noise."""
+  34         print(f"[{BOT_NAME}] Calibrating voice input...")
+  35         with self.microphone as source:
+  36             self.recognizer.adjust_for_ambient_noise(source, duration=1)
+  37 
+  38     def _audio_to_wav_bytes(self, audio: sr.AudioData) -> bytes:
+  39         """Convert SpeechRecognition AudioData to WAV bytes."""
+  40         wav_io = io.BytesIO()
+  41         with wave.open(wav_io, 'wb') as wav_file:
+  42             wav_file.setnchannels(1)
+  43             wav_file.setsampwidth(audio.sample_width)
+  44             wav_file.setframerate(audio.sample_rate)
+  45             wav_file.writeframes(audio.get_raw_data())
+  46         wav_io.seek(0)
+  47         return wav_io.read()
+  48 
+  49     def transcribe_with_whisper(self, audio: sr.AudioData) -> Optional[str]:
+  50         """
+  51         Transcribe audio using OpenAI's Whisper API.
+  52         Returns None if transcription fails.
+  53         """
+  54         if not self.openai_client:
+  55             return None
+  56 
+  57         try:
+  58             # Convert audio to WAV format
+  59             wav_bytes = self._audio_to_wav_bytes(audio)
+  60 
+  61             # Create a temporary file for the API
+  62             with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
+  63                 tmp_file.write(wav_bytes)
+  64                 tmp_path = tmp_file.name
+  65 
+  66             # Transcribe with Whisper
+  67             with open(tmp_path, "rb") as audio_file:
+  68                 response = self.openai_client.audio.transcriptions.create(
+  69                     model=VoiceConfig.WHISPER_MODEL,
+  70                     file=audio_file,
+  71                     response_format="text"
+  72                 )
+  73 
+  74             # Clean up temp file
+  75             Path(tmp_path).unlink(missing_ok=True)
+  76 
+  77             return response.strip() if response else None
+  78 
+  79         except Exception as e:
+  80             print(f"[{BOT_NAME}] Whisper transcription error: {e}")
+  81             return None
+  82 
+  83     def transcribe_with_google(self, audio: sr.AudioData) -> Optional[str]:
+  84         """
+  85         Transcribe audio using Google's free speech recognition.
+  86         Fallback option.
+  87         """
+  88         try:
+  89             text = self.recognizer.recognize_google(audio)
+  90             return text.strip() if text else None
+  91         except sr.UnknownValueError:
+  92             return None
+  93         except sr.RequestError as e:
+  94             print(f"[{BOT_NAME}] Google recognition error: {e}")
+  95             return None
+  96 
+  97     def listen_and_transcribe(self, timeout: int = 10, phrase_limit: int = 30) -> Optional[str]:
+  98         """
+  99         Listen for speech and transcribe it.
+ 100 
+ 101         Args:
+ 102             timeout: Max seconds to wait for speech to begin
+ 103             phrase_limit: Max seconds for the phrase
+ 104 
+ 105         Returns:
+ 106             Transcribed text or None if failed
+ 107         """
+ 108         try:
+ 109             with self.microphone as source:
+ 110                 print(f"[{BOT_NAME}] Listening...")
+ 111                 audio = self.recognizer.listen(
+ 112                     source,
+ 113                     timeout=timeout,
+ 114                     phrase_time_limit=phrase_limit
+ 115                 )
+ 116 
+ 117             # Try Whisper first (higher quality)
+ 118             text = self.transcribe_with_whisper(audio)
+ 119 
+ 120             # Fall back to Google if Whisper fails
+ 121             if text is None:
+ 122                 print(f"[{BOT_NAME}] Falling back to Google transcription...")
+ 123                 text = self.transcribe_with_google(audio)
+ 124 
+ 125             if text:
+ 126                 print(f"[{BOT_NAME}] Transcribed: '{text}'")
+ 127 
+ 128             return text
+ 129 
+ 130         except sr.WaitTimeoutError:
+ 131             print(f"[{BOT_NAME}] No speech detected (timeout)")
+ 132             return None
+ 133         except Exception as e:
+ 134             print(f"[{BOT_NAME}] Listen error: {e}")
+ 135             return None
+ 136 
+ 137     def transcribe_file(self, audio_path: str) -> Optional[str]:
+ 138         """
+ 139         Transcribe an audio file.
+ 140 
+ 141         Args:
+ 142             audio_path: Path to audio file (WAV, MP3, etc.)
+ 143 
+ 144         Returns:
+ 145             Transcribed text or None
+ 146         """
+ 147         if not self.openai_client:
+ 148             print(f"[{BOT_NAME}] OpenAI client not available for file transcription")
+ 149             return None
+ 150 
+ 151         try:
+ 152             with open(audio_path, "rb") as audio_file:
+ 153                 response = self.openai_client.audio.transcriptions.create(
+ 154                     model=VoiceConfig.WHISPER_MODEL,
+ 155                     file=audio_file,
+ 156                     response_format="text"
+ 157                 )
+ 158             return response.strip() if response else None
+ 159 
+ 160         except Exception as e:
+ 161             print(f"[{BOT_NAME}] File transcription error: {e}")
+ 162             return None
+ 163 
+ 164 
+ 165 if __name__ == "__main__":
+ 166     # Test voice input
+ 167     voice_input = VoiceInput()
+ 168 
+ 169     print("Say something...")
+ 170     text = voice_input.listen_and_transcribe()
+ 171 
+ 172     if text:
+ 173         print(f"\n✅ You said: '{text}'")
+ 174     else:
+ 175         print("\n❌ Could not transcribe speech")
