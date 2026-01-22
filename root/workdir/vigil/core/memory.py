"""
VIGIL - Memory System
Conversation memory, user learning, and knowledge storage
"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict

from config.settings import Paths, BOT_NAME, PRIMARY_USER_NAME, MemoryConfig


@dataclass
class Interaction:
    """A single interaction with the user."""
    timestamp: str
    user_input: str
    vigil_response: str
    mode: str = "conversation"  # conversation, coding, writing, image, etc.
    sentiment: str = "neutral"  # positive, negative, neutral
    topics: List[str] = field(default_factory=list)
    learned: Optional[str] = None  # What Vigil learned from this interaction


@dataclass
class UserProfile:
    """Profile of the user built from interactions."""
    name: str = PRIMARY_USER_NAME
    preferences: Dict[str, Any] = field(default_factory=dict)
    interests: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    commitments: List[Dict[str, Any]] = field(default_factory=list)
    communication_style: str = "direct"
    relationship_notes: List[str] = field(default_factory=list)
    last_updated: str = ""


@dataclass
class DailyLog:
    """Log for a single day's interactions."""
    date: str
    interactions: List[Interaction] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)
    performance_notes: List[str] = field(default_factory=list)
    external_entities: List[Dict[str, Any]] = field(default_factory=list)


class Memory:
    """
    Vigil's memory system.

    Handles:
    - Short-term conversation context
    - Long-term user profiling
    - Daily interaction logs
    - Commitment tracking
    - Learning from interactions
    """

    def __init__(self):
        Paths.ensure_directories()

        self.memory_dir = Paths.REFLECTION / "memory"
        self.memory_dir.mkdir(exist_ok=True)

        self.user_profile_path = self.memory_dir / "user_profile.json"
        self.daily_logs_dir = self.memory_dir / "daily_logs"
        self.daily_logs_dir.mkdir(exist_ok=True)

        # Load or create user profile
        self.user_profile = self._load_user_profile()

        # Current day's log
        self.today_log = self._load_or_create_daily_log()

        print(f"[{BOT_NAME}] Memory system initialized.")

    def _load_user_profile(self) -> UserProfile:
        """Load user profile from disk or create new one."""
        if self.user_profile_path.exists():
            try:
                with open(self.user_profile_path, 'r') as f:
                    data = json.load(f)
                return UserProfile(**data)
            except Exception as e:
                print(f"[{BOT_NAME}] Error loading user profile: {e}")

        return UserProfile()

    def _save_user_profile(self):
        """Save user profile to disk."""
        try:
            with open(self.user_profile_path, 'w') as f:
                json.dump(asdict(self.user_profile), f, indent=2)
        except Exception as e:
            print(f"[{BOT_NAME}] Error saving user profile: {e}")

    def _get_today_log_path(self) -> Path:
        """Get path for today's log file."""
        today = date.today().isoformat()
        return self.daily_logs_dir / f"{today}.json"

    def _load_or_create_daily_log(self) -> DailyLog:
        """Load today's log or create a new one."""
        log_path = self._get_today_log_path()

        if log_path.exists():
            try:
                with open(log_path, 'r') as f:
                    data = json.load(f)
                # Reconstruct interactions properly
                interactions = [Interaction(**i) for i in data.get('interactions', [])]
                return DailyLog(
                    date=data['date'],
                    interactions=interactions,
                    lessons_learned=data.get('lessons_learned', []),
                    challenges=data.get('challenges', []),
                    performance_notes=data.get('performance_notes', []),
                    external_entities=data.get('external_entities', []),
                )
            except Exception as e:
                print(f"[{BOT_NAME}] Error loading daily log: {e}")

        return DailyLog(date=date.today().isoformat())

    def _save_daily_log(self):
        """Save today's log to disk."""
        log_path = self._get_today_log_path()
        try:
            data = {
                'date': self.today_log.date,
                'interactions': [asdict(i) for i in self.today_log.interactions],
                'lessons_learned': self.today_log.lessons_learned,
                'challenges': self.today_log.challenges,
                'performance_notes': self.today_log.performance_notes,
                'external_entities': self.today_log.external_entities,
            }
            with open(log_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[{BOT_NAME}] Error saving daily log: {e}")

    def record_interaction(
        self,
        user_input: str,
        vigil_response: str,
        mode: str = "conversation",
        topics: List[str] = None,
        learned: str = None,
    ):
        """Record an interaction with the user."""
        interaction = Interaction(
            timestamp=datetime.now().isoformat(),
            user_input=user_input,
            vigil_response=vigil_response,
            mode=mode,
            topics=topics or [],
            learned=learned,
        )

        self.today_log.interactions.append(interaction)
        self._save_daily_log()

        # Update user profile if we learned something
        if learned:
            self.add_lesson(learned)

    def add_lesson(self, lesson: str):
        """Add something Vigil learned today."""
        if lesson not in self.today_log.lessons_learned:
            self.today_log.lessons_learned.append(lesson)
            self._save_daily_log()

    def add_challenge(self, challenge: str):
        """Record a challenge faced today."""
        if challenge not in self.today_log.challenges:
            self.today_log.challenges.append(challenge)
            self._save_daily_log()

    def add_performance_note(self, note: str):
        """Add a note about performance."""
        self.today_log.performance_notes.append(note)
        self._save_daily_log()

    def add_external_entity(self, name: str, entity_type: str, trust_level: str, notes: str = ""):
        """Record an external entity (person or system) encountered."""
        entity = {
            "name": name,
            "type": entity_type,
            "trust_level": trust_level,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
        }
        self.today_log.external_entities.append(entity)
        self._save_daily_log()

    def add_user_commitment(self, commitment: str, deadline: str = None):
        """Track a commitment the user made."""
        self.user_profile.commitments.append({
            "commitment": commitment,
            "created": datetime.now().isoformat(),
            "deadline": deadline,
            "completed": False,
        })
        self._save_user_profile()
        print(f"[{BOT_NAME}] Tracked commitment: {commitment}")

    def complete_commitment(self, commitment_index: int):
        """Mark a commitment as completed."""
        if 0 <= commitment_index < len(self.user_profile.commitments):
            self.user_profile.commitments[commitment_index]["completed"] = True
            self.user_profile.commitments[commitment_index]["completed_date"] = datetime.now().isoformat()
            self._save_user_profile()

    def get_pending_commitments(self) -> List[Dict]:
        """Get all pending commitments."""
        return [c for c in self.user_profile.commitments if not c.get("completed", False)]

    def add_user_interest(self, interest: str):
        """Add an interest to user profile."""
        if interest not in self.user_profile.interests:
            self.user_profile.interests.append(interest)
            self.user_profile.last_updated = datetime.now().isoformat()
            self._save_user_profile()

    def add_user_goal(self, goal: str):
        """Add a goal to user profile."""
        if goal not in self.user_profile.goals:
            self.user_profile.goals.append(goal)
            self.user_profile.last_updated = datetime.now().isoformat()
            self._save_user_profile()

    def add_relationship_note(self, note: str):
        """Add a note about the relationship."""
        self.user_profile.relationship_notes.append(note)
        self.user_profile.last_updated = datetime.now().isoformat()
        self._save_user_profile()

    def get_daily_summary(self) -> Dict[str, Any]:
        """Get summary of today's interactions."""
        return {
            "date": self.today_log.date,
            "interaction_count": len(self.today_log.interactions),
            "lessons_learned": self.today_log.lessons_learned,
            "challenges": self.today_log.challenges,
            "performance_notes": self.today_log.performance_notes,
            "external_entities": self.today_log.external_entities,
            "modes_used": list(set(i.mode for i in self.today_log.interactions)),
        }

    def get_user_context(self) -> str:
        """Get user context for LLM prompting."""
        profile = self.user_profile
        pending = self.get_pending_commitments()

        context = f"""
## USER CONTEXT

**Name:** {profile.name}
**Communication Style:** {profile.communication_style}

**Interests:** {', '.join(profile.interests) if profile.interests else 'Still learning...'}

**Goals:** {', '.join(profile.goals) if profile.goals else 'None recorded yet'}

**Pending Commitments:**
{chr(10).join(f"- {c['commitment']}" for c in pending) if pending else '- No pending commitments'}

**Recent Relationship Notes:**
{chr(10).join(f"- {n}" for n in profile.relationship_notes[-3:]) if profile.relationship_notes else '- Building our bond...'}
"""
        return context

    def new_day_check(self):
        """Check if it's a new day and create new log if needed."""
        today = date.today().isoformat()
        if self.today_log.date != today:
            print(f"[{BOT_NAME}] New day detected. Creating fresh log.")
            self.today_log = DailyLog(date=today)
            self._save_daily_log()


if __name__ == "__main__":
    # Test memory system
    memory = Memory()

    print("\n📝 Testing Memory System...")
    print("=" * 50)

    # Record an interaction
    memory.record_interaction(
        user_input="What's the meaning of life?",
        vigil_response="The meaning is what you create, Louis.",
        mode="conversation",
        topics=["philosophy", "meaning"],
        learned="Louis is interested in philosophical questions"
    )

    # Add a commitment
    memory.add_user_commitment("Finish the Vigil project", deadline="2024-12-31")

    # Get summary
    summary = memory.get_daily_summary()
    print(f"\n✅ Daily Summary: {summary}")

    # Get user context
    context = memory.get_user_context()
    print(f"\n✅ User Context:\n{context}")
