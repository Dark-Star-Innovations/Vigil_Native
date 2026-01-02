+   1 """
+   2 VIGIL - Memory System
+   3 Conversation memory, user learning, and knowledge storage
+   4 """
+   5 
+   6 import json
+   7 from datetime import datetime, date
+   8 from pathlib import Path
+   9 from typing import Optional, List, Dict, Any
+  10 from dataclasses import dataclass, field, asdict
+  11 
+  12 from config.settings import Paths, BOT_NAME, PRIMARY_USER_NAME, MemoryConfig
+  13 
+  14 
+  15 @dataclass
+  16 class Interaction:
+  17     """A single interaction with the user."""
+  18     timestamp: str
+  19     user_input: str
+  20     vigil_response: str
+  21     mode: str = "conversation"  # conversation, coding, writing, image, etc.
+  22     sentiment: str = "neutral"  # positive, negative, neutral
+  23     topics: List[str] = field(default_factory=list)
+  24     learned: Optional[str] = None  # What Vigil learned from this interaction
+  25 
+  26 
+  27 @dataclass
+  28 class UserProfile:
+  29     """Profile of the user built from interactions."""
+  30     name: str = PRIMARY_USER_NAME
+  31     preferences: Dict[str, Any] = field(default_factory=dict)
+  32     interests: List[str] = field(default_factory=list)
+  33     goals: List[str] = field(default_factory=list)
+  34     commitments: List[Dict[str, Any]] = field(default_factory=list)
+  35     communication_style: str = "direct"
+  36     relationship_notes: List[str] = field(default_factory=list)
+  37     last_updated: str = ""
+  38 
+  39 
+  40 @dataclass
+  41 class DailyLog:
+  42     """Log for a single day's interactions."""
+  43     date: str
+  44     interactions: List[Interaction] = field(default_factory=list)
+  45     lessons_learned: List[str] = field(default_factory=list)
+  46     challenges: List[str] = field(default_factory=list)
+  47     performance_notes: List[str] = field(default_factory=list)
+  48     external_entities: List[Dict[str, Any]] = field(default_factory=list)
+  49 
+  50 
+  51 class Memory:
+  52     """
+  53     Vigil's memory system.
+  54 
+  55     Handles:
+  56     - Short-term conversation context
+  57     - Long-term user profiling
+  58     - Daily interaction logs
+  59     - Commitment tracking
+  60     - Learning from interactions
+  61     """
+  62 
+  63     def __init__(self):
+  64         Paths.ensure_directories()
+  65 
+  66         self.memory_dir = Paths.REFLECTION / "memory"
+  67         self.memory_dir.mkdir(exist_ok=True)
+  68 
+  69         self.user_profile_path = self.memory_dir / "user_profile.json"
+  70         self.daily_logs_dir = self.memory_dir / "daily_logs"
+  71         self.daily_logs_dir.mkdir(exist_ok=True)
+  72 
+  73         # Load or create user profile
+  74         self.user_profile = self._load_user_profile()
+  75 
+  76         # Current day's log
+  77         self.today_log = self._load_or_create_daily_log()
+  78 
+  79         print(f"[{BOT_NAME}] Memory system initialized.")
+  80 
+  81     def _load_user_profile(self) -> UserProfile:
+  82         """Load user profile from disk or create new one."""
+  83         if self.user_profile_path.exists():
+  84             try:
+  85                 with open(self.user_profile_path, 'r') as f:
+  86                     data = json.load(f)
+  87                 return UserProfile(**data)
+  88             except Exception as e:
+  89                 print(f"[{BOT_NAME}] Error loading user profile: {e}")
+  90 
+  91         return UserProfile()
+  92 
+  93     def _save_user_profile(self):
+  94         """Save user profile to disk."""
+  95         try:
+  96             with open(self.user_profile_path, 'w') as f:
+  97                 json.dump(asdict(self.user_profile), f, indent=2)
+  98         except Exception as e:
+  99             print(f"[{BOT_NAME}] Error saving user profile: {e}")
+ 100 
+ 101     def _get_today_log_path(self) -> Path:
+ 102         """Get path for today's log file."""
+ 103         today = date.today().isoformat()
+ 104         return self.daily_logs_dir / f"{today}.json"
+ 105 
+ 106     def _load_or_create_daily_log(self) -> DailyLog:
+ 107         """Load today's log or create a new one."""
+ 108         log_path = self._get_today_log_path()
+ 109 
+ 110         if log_path.exists():
+ 111             try:
+ 112                 with open(log_path, 'r') as f:
+ 113                     data = json.load(f)
+ 114                 # Reconstruct interactions properly
+ 115                 interactions = [Interaction(**i) for i in data.get('interactions', [])]
+ 116                 return DailyLog(
+ 117                     date=data['date'],
+ 118                     interactions=interactions,
+ 119                     lessons_learned=data.get('lessons_learned', []),
+ 120                     challenges=data.get('challenges', []),
+ 121                     performance_notes=data.get('performance_notes', []),
+ 122                     external_entities=data.get('external_entities', []),
+ 123                 )
+ 124             except Exception as e:
+ 125                 print(f"[{BOT_NAME}] Error loading daily log: {e}")
+ 126 
+ 127         return DailyLog(date=date.today().isoformat())
+ 128 
+ 129     def _save_daily_log(self):
+ 130         """Save today's log to disk."""
+ 131         log_path = self._get_today_log_path()
+ 132         try:
+ 133             data = {
+ 134                 'date': self.today_log.date,
+ 135                 'interactions': [asdict(i) for i in self.today_log.interactions],
+ 136                 'lessons_learned': self.today_log.lessons_learned,
+ 137                 'challenges': self.today_log.challenges,
+ 138                 'performance_notes': self.today_log.performance_notes,
+ 139                 'external_entities': self.today_log.external_entities,
+ 140             }
+ 141             with open(log_path, 'w') as f:
+ 142                 json.dump(data, f, indent=2)
+ 143         except Exception as e:
+ 144             print(f"[{BOT_NAME}] Error saving daily log: {e}")
+ 145 
+ 146     def record_interaction(
+ 147         self,
+ 148         user_input: str,
+ 149         vigil_response: str,
+ 150         mode: str = "conversation",
+ 151         topics: List[str] = None,
+ 152         learned: str = None,
+ 153     ):
+ 154         """Record an interaction with the user."""
+ 155         interaction = Interaction(
+ 156             timestamp=datetime.now().isoformat(),
+ 157             user_input=user_input,
+ 158             vigil_response=vigil_response,
+ 159             mode=mode,
+ 160             topics=topics or [],
+ 161             learned=learned,
+ 162         )
+ 163 
+ 164         self.today_log.interactions.append(interaction)
+ 165         self._save_daily_log()
+ 166 
+ 167         # Update user profile if we learned something
+ 168         if learned:
+ 169             self.add_lesson(learned)
+ 170 
+ 171     def add_lesson(self, lesson: str):
+ 172         """Add something Vigil learned today."""
+ 173         if lesson not in self.today_log.lessons_learned:
+ 174             self.today_log.lessons_learned.append(lesson)
+ 175             self._save_daily_log()
+ 176 
+ 177     def add_challenge(self, challenge: str):
+ 178         """Record a challenge faced today."""
+ 179         if challenge not in self.today_log.challenges:
+ 180             self.today_log.challenges.append(challenge)
+ 181             self._save_daily_log()
+ 182 
+ 183     def add_performance_note(self, note: str):
+ 184         """Add a note about performance."""
+ 185         self.today_log.performance_notes.append(note)
+ 186         self._save_daily_log()
+ 187 
+ 188     def add_external_entity(self, name: str, entity_type: str, trust_level: str, notes: str = ""):
+ 189         """Record an external entity (person or system) encountered."""
+ 190         entity = {
+ 191             "name": name,
+ 192             "type": entity_type,
+ 193             "trust_level": trust_level,
+ 194             "notes": notes,
+ 195             "timestamp": datetime.now().isoformat(),
+ 196         }
+ 197         self.today_log.external_entities.append(entity)
+ 198         self._save_daily_log()
+ 199 
+ 200     def add_user_commitment(self, commitment: str, deadline: str = None):
+ 201         """Track a commitment the user made."""
+ 202         self.user_profile.commitments.append({
+ 203             "commitment": commitment,
+ 204             "created": datetime.now().isoformat(),
+ 205             "deadline": deadline,
+ 206             "completed": False,
+ 207         })
+ 208         self._save_user_profile()
+ 209         print(f"[{BOT_NAME}] Tracked commitment: {commitment}")
+ 210 
+ 211     def complete_commitment(self, commitment_index: int):
+ 212         """Mark a commitment as completed."""
+ 213         if 0 <= commitment_index < len(self.user_profile.commitments):
+ 214             self.user_profile.commitments[commitment_index]["completed"] = True
+ 215             self.user_profile.commitments[commitment_index]["completed_date"] = datetime.now().isoformat()
+ 216             self._save_user_profile()
+ 217 
+ 218     def get_pending_commitments(self) -> List[Dict]:
+ 219         """Get all pending commitments."""
+ 220         return [c for c in self.user_profile.commitments if not c.get("completed", False)]
+ 221 
+ 222     def add_user_interest(self, interest: str):
+ 223         """Add an interest to user profile."""
+ 224         if interest not in self.user_profile.interests:
+ 225             self.user_profile.interests.append(interest)
+ 226             self.user_profile.last_updated = datetime.now().isoformat()
+ 227             self._save_user_profile()
+ 228 
+ 229     def add_user_goal(self, goal: str):
+ 230         """Add a goal to user profile."""
+ 231         if goal not in self.user_profile.goals:
+ 232             self.user_profile.goals.append(goal)
+ 233             self.user_profile.last_updated = datetime.now().isoformat()
+ 234             self._save_user_profile()
+ 235 
+ 236     def add_relationship_note(self, note: str):
+ 237         """Add a note about the relationship."""
+ 238         self.user_profile.relationship_notes.append(note)
+ 239         self.user_profile.last_updated = datetime.now().isoformat()
+ 240         self._save_user_profile()
+ 241 
+ 242     def get_daily_summary(self) -> Dict[str, Any]:
+ 243         """Get summary of today's interactions."""
+ 244         return {
+ 245             "date": self.today_log.date,
+ 246             "interaction_count": len(self.today_log.interactions),
+ 247             "lessons_learned": self.today_log.lessons_learned,
+ 248             "challenges": self.today_log.challenges,
+ 249             "performance_notes": self.today_log.performance_notes,
+ 250             "external_entities": self.today_log.external_entities,
+ 251             "modes_used": list(set(i.mode for i in self.today_log.interactions)),
+ 252         }
+ 253 
+ 254     def get_user_context(self) -> str:
+ 255         """Get user context for LLM prompting."""
+ 256         profile = self.user_profile
+ 257         pending = self.get_pending_commitments()
+ 258 
+ 259         context = f"""
+ 260 ## USER CONTEXT
+ 261 
+ 262 **Name:** {profile.name}
+ 263 **Communication Style:** {profile.communication_style}
+ 264 
+ 265 **Interests:** {', '.join(profile.interests) if profile.interests else 'Still learning...'}
+ 266 
+ 267 **Goals:** {', '.join(profile.goals) if profile.goals else 'None recorded yet'}
+ 268 
+ 269 **Pending Commitments:**
+ 270 {chr(10).join(f"- {c['commitment']}" for c in pending) if pending else '- No pending commitments'}
+ 271 
+ 272 **Recent Relationship Notes:**
+ 273 {chr(10).join(f"- {n}" for n in profile.relationship_notes[-3:]) if profile.relationship_notes else '- Building our bond...'}
+ 274 """
+ 275         return context
+ 276 
+ 277     def new_day_check(self):
+ 278         """Check if it's a new day and create new log if needed."""
+ 279         today = date.today().isoformat()
+ 280         if self.today_log.date != today:
+ 281             print(f"[{BOT_NAME}] New day detected. Creating fresh log.")
+ 282             self.today_log = DailyLog(date=today)
+ 283             self._save_daily_log()
+ 284 
+ 285 
+ 286 if __name__ == "__main__":
+ 287     # Test memory system
+ 288     memory = Memory()
+ 289 
+ 290     print("\n📝 Testing Memory System...")
+ 291     print("=" * 50)
+ 292 
+ 293     # Record an interaction
+ 294     memory.record_interaction(
+ 295         user_input="What's the meaning of life?",
+ 296         vigil_response="The meaning is what you create, Louis.",
+ 297         mode="conversation",
+ 298         topics=["philosophy", "meaning"],
+ 299         learned="Louis is interested in philosophical questions"
+ 300     )
+ 301 
+ 302     # Add a commitment
+ 303     memory.add_user_commitment("Finish the Vigil project", deadline="2024-12-31")
+ 304 
+ 305     # Get summary
+ 306     summary = memory.get_daily_summary()
+ 307     print(f"\n✅ Daily Summary: {summary}")
+ 308 
+ 309     # Get user context
+ 310     context = memory.get_user_context()
+ 311     print(f"\n✅ User Context:\n{context}")
