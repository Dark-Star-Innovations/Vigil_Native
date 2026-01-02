+   1 """
+   2 VIGIL - Voice Output (Text-to-Speech)
+   3 Premium voice using ElevenLabs with Windows SAPI fallback
+   4 """
+   5 
+   6 import io
+   7 import tempfile
+   8 import threading
+   9 from typing import Optional
+  10 from pathlib import Path
+  11 
+  12 from config.settings import ELEVENLABS_API_KEY, VoiceConfig, BOT_NAME
+  13 
+  14 
+  15 class VoiceOutput:
+  16     """
+  17     Handles text-to-speech conversion.
+  18     Primary: ElevenLabs API (premium, natural voice)
+  19     Fallback: Windows SAPI (free, offline)
+  20     """
+  21 
+  22     def __init__(self):
+  23         self.elevenlabs_available = bool(ELEVENLABS_API_KEY)
+  24         self.pyttsx3_engine = None
+  25 
+  26         # Initialize ElevenLabs if available
+  27         if self.elevenlabs_available:
+  28             try:
+  29                 from elevenlabs import ElevenLabs
+  30                 self.elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
+  31                 print(f"[{BOT_NAME}] ElevenLabs voice initialized.")
+  32             except ImportError:
+  33                 print(f"[{BOT_NAME}] ElevenLabs not installed. Using fallback.")
+  34                 self.elevenlabs_available = False
+  35             except Exception as e:
+  36                 print(f"[{BOT_NAME}] ElevenLabs init error: {e}. Using fallback.")
+  37                 self.elevenlabs_available = False
+  38 
+  39         # Initialize fallback TTS
+  40         self._init_fallback()
+  41 
+  42     def _init_fallback(self):
+  43         """Initialize pyttsx3 as fallback TTS."""
+  44         try:
+  45             import pyttsx3
+  46             self.pyttsx3_engine = pyttsx3.init()
+  47             # Configure voice
+  48             voices = self.pyttsx3_engine.getProperty('voices')
+  49             # Try to find a male voice
+  50             for voice in voices:
+  51                 if 'male' in voice.name.lower() or 'david' in voice.name.lower():
+  52                     self.pyttsx3_engine.setProperty('voice', voice.id)
+  53                     break
+  54             self.pyttsx3_engine.setProperty('rate', 175)  # Speed
+  55             self.pyttsx3_engine.setProperty('volume', 0.9)
+  56             print(f"[{BOT_NAME}] Fallback TTS (pyttsx3) initialized.")
+  57         except Exception as e:
+  58             print(f"[{BOT_NAME}] Fallback TTS init error: {e}")
+  59             self.pyttsx3_engine = None
+  60 
+  61     def speak_elevenlabs(self, text: str) -> bool:
+  62         """
+  63         Speak using ElevenLabs API.
+  64         Returns True if successful.
+  65         """
+  66         if not self.elevenlabs_available:
+  67             return False
+  68 
+  69         try:
+  70             from elevenlabs import play, Voice, VoiceSettings
+  71 
+  72             # Generate audio
+  73             audio = self.elevenlabs_client.text_to_speech.convert(
+  74                 text=text,
+  75                 voice_id=VoiceConfig.ELEVENLABS_VOICE_ID,
+  76                 model_id=VoiceConfig.ELEVENLABS_MODEL,
+  77             )
+  78 
+  79             # Play the audio
+  80             # Convert generator to bytes if needed
+  81             if hasattr(audio, '__iter__') and not isinstance(audio, bytes):
+  82                 audio_bytes = b''.join(audio)
+  83             else:
+  84                 audio_bytes = audio
+  85 
+  86             # Save to temp file and play
+  87             with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
+  88                 tmp_file.write(audio_bytes)
+  89                 tmp_path = tmp_file.name
+  90 
+  91             # Play using pygame or fallback
+  92             self._play_audio_file(tmp_path)
+  93 
+  94             # Cleanup
+  95             Path(tmp_path).unlink(missing_ok=True)
+  96 
+  97             return True
+  98 
+  99         except Exception as e:
+ 100             print(f"[{BOT_NAME}] ElevenLabs speak error: {e}")
+ 101             return False
+ 102 
+ 103     def _play_audio_file(self, file_path: str):
+ 104         """Play an audio file using available player."""
+ 105         try:
+ 106             # Try pygame first
+ 107             import pygame
+ 108             pygame.mixer.init()
+ 109             pygame.mixer.music.load(file_path)
+ 110             pygame.mixer.music.play()
+ 111             while pygame.mixer.music.get_busy():
+ 112                 pygame.time.wait(100)
+ 113             pygame.mixer.quit()
+ 114         except ImportError:
+ 115             # Fallback to playsound
+ 116             try:
+ 117                 from playsound import playsound
+ 118                 playsound(file_path)
+ 119             except ImportError:
+ 120                 # Last resort: Windows command
+ 121                 import subprocess
+ 122                 import sys
+ 123                 if sys.platform == 'win32':
+ 124                     subprocess.run(
+ 125                         ['powershell', '-c', f'(New-Object Media.SoundPlayer "{file_path}").PlaySync()'],
+ 126                         capture_output=True
+ 127                     )
+ 128 
+ 129     def speak_pyttsx3(self, text: str) -> bool:
+ 130         """
+ 131         Speak using pyttsx3 (Windows SAPI).
+ 132         Returns True if successful.
+ 133         """
+ 134         if not self.pyttsx3_engine:
+ 135             return False
+ 136 
+ 137         try:
+ 138             self.pyttsx3_engine.say(text)
+ 139             self.pyttsx3_engine.runAndWait()
+ 140             return True
+ 141         except Exception as e:
+ 142             print(f"[{BOT_NAME}] pyttsx3 speak error: {e}")
+ 143             return False
+ 144 
+ 145     def speak(self, text: str, use_elevenlabs: bool = True) -> bool:
+ 146         """
+ 147         Speak the given text.
+ 148 
+ 149         Args:
+ 150             text: Text to speak
+ 151             use_elevenlabs: Whether to try ElevenLabs first
+ 152 
+ 153         Returns:
+ 154             True if speech was successful
+ 155         """
+ 156         if not text or not text.strip():
+ 157             return False
+ 158 
+ 159         print(f"[{BOT_NAME}] Speaking: '{text[:50]}...' " if len(text) > 50 else f"[{BOT_NAME}] Speaking: '{text}'")
+ 160 
+ 161         # Try ElevenLabs first
+ 162         if use_elevenlabs and self.elevenlabs_available:
+ 163             if self.speak_elevenlabs(text):
+ 164                 return True
+ 165             print(f"[{BOT_NAME}] ElevenLabs failed, falling back to pyttsx3...")
+ 166 
+ 167         # Fallback to pyttsx3
+ 168         return self.speak_pyttsx3(text)
+ 169 
+ 170     def speak_async(self, text: str, use_elevenlabs: bool = True):
+ 171         """
+ 172         Speak in a background thread (non-blocking).
+ 173         """
+ 174         thread = threading.Thread(
+ 175             target=self.speak,
+ 176             args=(text, use_elevenlabs),
+ 177             daemon=True
+ 178         )
+ 179         thread.start()
+ 180         return thread
+ 181 
+ 182     def set_voice(self, voice_id: str):
+ 183         """Change the ElevenLabs voice ID."""
+ 184         VoiceConfig.ELEVENLABS_VOICE_ID = voice_id
+ 185         print(f"[{BOT_NAME}] Voice changed to: {voice_id}")
+ 186 
+ 187     def list_elevenlabs_voices(self) -> list:
+ 188         """List available ElevenLabs voices."""
+ 189         if not self.elevenlabs_available:
+ 190             return []
+ 191 
+ 192         try:
+ 193             voices = self.elevenlabs_client.voices.get_all()
+ 194             return [(v.voice_id, v.name) for v in voices.voices]
+ 195         except Exception as e:
+ 196             print(f"[{BOT_NAME}] Could not list voices: {e}")
+ 197             return []
+ 198 
+ 199 
+ 200 if __name__ == "__main__":
+ 201     # Test voice output
+ 202     voice = VoiceOutput()
+ 203 
+ 204     test_text = "Hello Louis. I am Vigil, your watchful guardian. I am here to serve and protect."
+ 205 
+ 206     print("Testing voice output...")
+ 207     success = voice.speak(test_text)
+ 208 
+ 209     if success:
+ 210         print("✅ Voice output successful!")
+ 211     else:
+ 212         print("❌ Voice output failed.")
