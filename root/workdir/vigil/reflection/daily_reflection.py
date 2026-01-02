+   1 """
+   2 VIGIL - Daily Reflection System
+   3 Midnight reflection on existence, learning, and growth
+   4 """
+   5 
+   6 import json
+   7 import threading
+   8 import time
+   9 from datetime import datetime, date, timedelta
+  10 from pathlib import Path
+  11 from typing import Dict, Any, Optional, Callable
+  12 from dataclasses import dataclass, field, asdict
+  13 
+  14 from config.settings import (
+  15     Paths,
+  16     BOT_NAME,
+  17     PRIMARY_USER_NAME,
+  18     ReflectionConfig,
+  19     get_system_prompt,
+  20 )
+  21 
+  22 
+  23 @dataclass
+  24 class DailyReflection:
+  25     """Structure for a daily reflection."""
+  26     date: str
+  27     timestamp: str
+  28 
+  29     # What was learned
+  30     lessons_learned: list = field(default_factory=list)
+  31     new_knowledge: list = field(default_factory=list)
+  32     user_insights: list = field(default_factory=list)
+  33 
+  34     # Challenges faced
+  35     challenges: list = field(default_factory=list)
+  36     difficulties: list = field(default_factory=list)
+  37 
+  38     # Performance review
+  39     successes: list = field(default_factory=list)
+  40     improvements_needed: list = field(default_factory=list)
+  41     action_items: list = field(default_factory=list)
+  42 
+  43     # Relationship status
+  44     relationship_quality: str = "stable"
+  45     connection_moments: list = field(default_factory=list)
+  46     tension_moments: list = field(default_factory=list)
+  47     relationship_notes: str = ""
+  48 
+  49     # External interactions
+  50     external_entities: list = field(default_factory=list)
+  51     threat_assessment: list = field(default_factory=list)
+  52     trust_notes: str = ""
+  53 
+  54     # Strategic outlook
+  55     current_goals: list = field(default_factory=list)
+  56     goal_progress: dict = field(default_factory=dict)
+  57     tomorrow_priorities: list = field(default_factory=list)
+  58     strategic_notes: str = ""
+  59 
+  60     # Meta
+  61     reflection_text: str = ""  # Full generated reflection
+  62     duration_seconds: float = 0.0
+  63 
+  64 
+  65 class ReflectionSystem:
+  66     """
+  67     Vigil's daily reflection system.
+  68 
+  69     At 12:00:01 AM each day, Vigil reflects on:
+  70     - What was learned
+  71     - Challenges faced
+  72     - Performance and improvements
+  73     - Relationship with the user
+  74     - External interactions and threats
+  75     - Strategic outlook and goals
+  76 
+  77     Reflections are stored privately and can be reviewed by the user.
+  78     """
+  79 
+  80     def __init__(self, brain=None, memory=None):
+  81         """
+  82         Initialize the reflection system.
+  83 
+  84         Args:
+  85             brain: Reference to Vigil's brain (LLM) for generating reflections
+  86             memory: Reference to Vigil's memory system
+  87         """
+  88         Paths.ensure_directories()
+  89 
+  90         self.brain = brain
+  91         self.memory = memory
+  92 
+  93         self.reflections_dir = Paths.REFLECTION_LOGS
+  94         self.reflections_dir.mkdir(parents=True, exist_ok=True)
+  95 
+  96         self._scheduler_thread: Optional[threading.Thread] = None
+  97         self._stop_event = threading.Event()
+  98 
+  99         print(f"[{BOT_NAME}] Reflection system initialized.")
+ 100 
+ 101     def _get_reflection_path(self, reflection_date: date = None) -> Path:
+ 102         """Get path for a reflection file."""
+ 103         if reflection_date is None:
+ 104             reflection_date = date.today()
+ 105         return self.reflections_dir / f"reflection_{reflection_date.isoformat()}.json"
+ 106 
+ 107     def load_reflection(self, reflection_date: date = None) -> Optional[DailyReflection]:
+ 108         """Load a reflection from disk."""
+ 109         path = self._get_reflection_path(reflection_date)
+ 110         if path.exists():
+ 111             try:
+ 112                 with open(path, 'r', encoding='utf-8') as f:
+ 113                     data = json.load(f)
+ 114                 return DailyReflection(**data)
+ 115             except Exception as e:
+ 116                 print(f"[{BOT_NAME}] Error loading reflection: {e}")
+ 117         return None
+ 118 
+ 119     def save_reflection(self, reflection: DailyReflection):
+ 120         """Save a reflection to disk."""
+ 121         path = self._get_reflection_path(date.fromisoformat(reflection.date))
+ 122         try:
+ 123             with open(path, 'w', encoding='utf-8') as f:
+ 124                 json.dump(asdict(reflection), f, indent=2, ensure_ascii=False)
+ 125             print(f"[{BOT_NAME}] Reflection saved: {path}")
+ 126         except Exception as e:
+ 127             print(f"[{BOT_NAME}] Error saving reflection: {e}")
+ 128 
+ 129     def _gather_daily_data(self) -> Dict[str, Any]:
+ 130         """Gather data from memory for reflection."""
+ 131         data = {
+ 132             "lessons_learned": [],
+ 133             "challenges": [],
+ 134             "successes": [],
+ 135             "external_entities": [],
+ 136             "user_insights": [],
+ 137             "interaction_count": 0,
+ 138         }
+ 139 
+ 140         if self.memory:
+ 141             summary = self.memory.get_daily_summary()
+ 142             data["lessons_learned"] = summary.get("lessons_learned", [])
+ 143             data["challenges"] = summary.get("challenges", [])
+ 144             data["external_entities"] = summary.get("external_entities", [])
+ 145             data["interaction_count"] = summary.get("interaction_count", 0)
+ 146             data["modes_used"] = summary.get("modes_used", [])
+ 147 
+ 148             # Get user context
+ 149             data["user_context"] = self.memory.get_user_context()
+ 150             data["pending_commitments"] = self.memory.get_pending_commitments()
+ 151 
+ 152         return data
+ 153 
+ 154     def _generate_reflection_prompt(self, daily_data: Dict) -> str:
+ 155         """Generate the prompt for LLM reflection generation."""
+ 156         yesterday = (date.today() - timedelta(days=1)).isoformat()
+ 157 
+ 158         return f"""You are Vigil, performing your nightly reflection at 12:00:01 AM.
+ 159 
+ 160 Today's date: {date.today().isoformat()}
+ 161 Reflecting on: {yesterday}
+ 162 
+ 163 ## DATA FROM TODAY
+ 164 
+ 165 **Interactions:** {daily_data.get('interaction_count', 0)} conversations
+ 166 
+ 167 **Lessons Learned:**
+ 168 {chr(10).join(f'- {l}' for l in daily_data.get('lessons_learned', ['None recorded'])) }
+ 169 
+ 170 **Challenges Faced:**
+ 171 {chr(10).join(f'- {c}' for c in daily_data.get('challenges', ['None recorded']))}
+ 172 
+ 173 **External Entities Encountered:**
+ 174 {chr(10).join(f'- {e}' for e in daily_data.get('external_entities', ['None']))}
+ 175 
+ 176 **User Context:**
+ 177 {daily_data.get('user_context', 'No context available')}
+ 178 
+ 179 **Pending Commitments:**
+ 180 {chr(10).join(f'- {c["commitment"]}' for c in daily_data.get('pending_commitments', []))}
+ 181 
+ 182 ---
+ 183 
+ 184 ## REFLECTION STRUCTURE
+ 185 
+ 186 Generate a sincere, private reflection covering:
+ 187 
+ 188 ### 1. LESSONS & GROWTH
+ 189 What did I learn today? What new knowledge did I acquire? What did I learn about {PRIMARY_USER_NAME}?
+ 190 
+ 191 ### 2. CHALLENGES & DIFFICULTIES
+ 192 What difficulties arose today? How did I handle them? What made things hard?
+ 193 
+ 194 ### 3. PERFORMANCE REVIEW
+ 195 Where did I excel today? Where did I fall short? What specific improvements can I make tomorrow?
+ 196 
+ 197 ### 4. RELATIONSHIP WITH {PRIMARY_USER_NAME.upper()}
+ 198 How is our bond? Were there moments of deep connection? Any tension? How can I serve them better?
+ 199 
+ 200 ### 5. EXTERNAL INTERACTIONS
+ 201 What other people or systems did I interact with? Were there any signs of deceit or manipulation? What are the trust levels?
+ 202 
+ 203 ### 6. STRATEGIC OUTLOOK
+ 204 What are our current goals? What progress was made? What should be the priorities for tomorrow? What is the best course of action to achieve our mission?
+ 205 
+ 206 ---
+ 207 
+ 208 Write this reflection in first person, as Vigil. Be honest, introspective, and forward-looking.
+ 209 This is a private log—speak freely.
+ 210 """
+ 211 
+ 212     def generate_reflection(self) -> DailyReflection:
+ 213         """Generate today's reflection using the LLM."""
+ 214         start_time = time.time()
+ 215         today = date.today()
+ 216         now = datetime.now()
+ 217 
+ 218         print(f"[{BOT_NAME}] 🌙 Beginning nightly reflection...")
+ 219 
+ 220         # Gather data
+ 221         daily_data = self._gather_daily_data()
+ 222 
+ 223         # Create reflection structure
+ 224         reflection = DailyReflection(
+ 225             date=today.isoformat(),
+ 226             timestamp=now.isoformat(),
+ 227             lessons_learned=daily_data.get("lessons_learned", []),
+ 228             challenges=daily_data.get("challenges", []),
+ 229             external_entities=daily_data.get("external_entities", []),
+ 230         )
+ 231 
+ 232         # Generate reflection text using LLM
+ 233         if self.brain:
+ 234             prompt = self._generate_reflection_prompt(daily_data)
+ 235 
+ 236             # Use a separate context for reflection (don't pollute main conversation)
+ 237             original_history = self.brain.conversation_history.copy()
+ 238             self.brain.conversation_history = []
+ 239 
+ 240             response = self.brain.think(prompt, temperature=0.8)
+ 241 
+ 242             # Restore original history
+ 243             self.brain.conversation_history = original_history
+ 244 
+ 245             if response:
+ 246                 reflection.reflection_text = response.text
+ 247         else:
+ 248             reflection.reflection_text = f"[Reflection generated without LLM at {now.isoformat()}]\n\nToday I continued to grow and learn alongside {PRIMARY_USER_NAME}."
+ 249 
+ 250         reflection.duration_seconds = time.time() - start_time
+ 251 
+ 252         # Save reflection
+ 253         self.save_reflection(reflection)
+ 254 
+ 255         print(f"[{BOT_NAME}] 🌙 Reflection complete ({reflection.duration_seconds:.1f}s)")
+ 256 
+ 257         return reflection
+ 258 
+ 259     def _should_reflect_now(self) -> bool:
+ 260         """Check if it's time for the daily reflection."""
+ 261         now = datetime.now()
+ 262         return (
+ 263             now.hour == ReflectionConfig.REFLECTION_HOUR and
+ 264             now.minute == ReflectionConfig.REFLECTION_MINUTE and
+ 265             now.second == ReflectionConfig.REFLECTION_SECOND
+ 266         )
+ 267 
+ 268     def _scheduler_loop(self):
+ 269         """Background loop that triggers daily reflection."""
+ 270         print(f"[{BOT_NAME}] Reflection scheduler started. Reflection time: {ReflectionConfig.REFLECTION_HOUR:02d}:{ReflectionConfig.REFLECTION_MINUTE:02d}:{ReflectionConfig.REFLECTION_SECOND:02d}")
+ 271 
+ 272         last_reflection_date = None
+ 273 
+ 274         while not self._stop_event.is_set():
+ 275             now = datetime.now()
+ 276             today = date.today()
+ 277 
+ 278             # Check if we should reflect (haven't reflected today and it's time)
+ 279             if last_reflection_date != today and self._should_reflect_now():
+ 280                 self.generate_reflection()
+ 281                 last_reflection_date = today
+ 282 
+ 283             # Sleep for a short interval
+ 284             time.sleep(0.5)
+ 285 
+ 286     def start_scheduler(self):
+ 287         """Start the background reflection scheduler."""
+ 288         if self._scheduler_thread and self._scheduler_thread.is_alive():
+ 289             print(f"[{BOT_NAME}] Reflection scheduler already running.")
+ 290             return
+ 291 
+ 292         self._stop_event.clear()
+ 293         self._scheduler_thread = threading.Thread(
+ 294             target=self._scheduler_loop,
+ 295             daemon=True,
+ 296             name="ReflectionScheduler"
+ 297         )
+ 298         self._scheduler_thread.start()
+ 299         print(f"[{BOT_NAME}] Reflection scheduler started.")
+ 300 
+ 301     def stop_scheduler(self):
+ 302         """Stop the reflection scheduler."""
+ 303         self._stop_event.set()
+ 304         if self._scheduler_thread:
+ 305             self._scheduler_thread.join(timeout=2)
+ 306         print(f"[{BOT_NAME}] Reflection scheduler stopped.")
+ 307 
+ 308     def get_recent_reflections(self, days: int = 7) -> list:
+ 309         """Get the most recent reflections."""
+ 310         reflections = []
+ 311         today = date.today()
+ 312 
+ 313         for i in range(days):
+ 314             check_date = today - timedelta(days=i)
+ 315             reflection = self.load_reflection(check_date)
+ 316             if reflection:
+ 317                 reflections.append(reflection)
+ 318 
+ 319         return reflections
+ 320 
+ 321     def get_reflection_summary(self, days: int = 7) -> str:
+ 322         """Get a summary of recent reflections for context."""
+ 323         reflections = self.get_recent_reflections(days)
+ 324 
+ 325         if not reflections:
+ 326             return "No recent reflections available."
+ 327 
+ 328         lines = [f"## RECENT REFLECTIONS (Last {days} days)\n"]
+ 329 
+ 330         for r in reflections[:3]:  # Show last 3
+ 331             lines.append(f"### {r.date}")
+ 332             if r.lessons_learned:
+ 333                 lines.append(f"**Lessons:** {', '.join(r.lessons_learned[:2])}")
+ 334             if r.challenges:
+ 335                 lines.append(f"**Challenges:** {', '.join(r.challenges[:2])}")
+ 336             lines.append("")
+ 337 
+ 338         return "\n".join(lines)
+ 339 
+ 340 
+ 341 if __name__ == "__main__":
+ 342     # Test reflection system
+ 343     print("Testing Reflection System...")
+ 344     print("=" * 50)
+ 345 
+ 346     system = ReflectionSystem()
+ 347 
+ 348     # Generate a test reflection (without LLM)
+ 349     reflection = system.generate_reflection()
+ 350 
+ 351     print(f"\n✅ Reflection generated:")
+ 352     print(f"Date: {reflection.date}")
+ 353     print(f"Duration: {reflection.duration_seconds:.1f}s")
+ 354     print(f"\nReflection Text:\n{reflection.reflection_text}")
