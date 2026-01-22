"""
VIGIL - Custom Knowledge Base
User-extensible knowledge storage and retrieval
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

from config.settings import Paths, BOT_NAME


@dataclass
class KnowledgeEntry:
    """A single piece of knowledge."""
    id: str
    title: str
    content: str
    category: str
    tags: List[str] = field(default_factory=list)
    source: str = ""
    created: str = ""
    updated: str = ""
    importance: int = 5  # 1-10 scale
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeBase:
    """
    Vigil's custom knowledge base.

    Allows storing and retrieving knowledge entries that can be:
    - Added by the user
    - Learned from interactions
    - Imported from files

    Knowledge is categorized and tagged for efficient retrieval.
    """

    def __init__(self):
        Paths.ensure_directories()

        self.kb_dir = Paths.KNOWLEDGE / "custom"
        self.kb_dir.mkdir(exist_ok=True)

        self.entries_file = self.kb_dir / "entries.json"
        self.entries: Dict[str, KnowledgeEntry] = {}

        self._load_entries()
        print(f"[{BOT_NAME}] Knowledge base initialized with {len(self.entries)} entries.")

    def _load_entries(self):
        """Load knowledge entries from disk."""
        if self.entries_file.exists():
            try:
                with open(self.entries_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for entry_id, entry_data in data.items():
                    self.entries[entry_id] = KnowledgeEntry(**entry_data)
            except Exception as e:
                print(f"[{BOT_NAME}] Error loading knowledge base: {e}")

    def _save_entries(self):
        """Save knowledge entries to disk."""
        try:
            data = {eid: asdict(entry) for eid, entry in self.entries.items()}
            with open(self.entries_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[{BOT_NAME}] Error saving knowledge base: {e}")

    def _generate_id(self) -> str:
        """Generate a unique ID for a new entry."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        count = len(self.entries)
        return f"kb_{timestamp}_{count}"

    def add_entry(
        self,
        title: str,
        content: str,
        category: str = "general",
        tags: List[str] = None,
        source: str = "",
        importance: int = 5,
        metadata: Dict = None,
    ) -> str:
        """
        Add a new knowledge entry.

        Returns the entry ID.
        """
        entry_id = self._generate_id()
        now = datetime.now().isoformat()

        entry = KnowledgeEntry(
            id=entry_id,
            title=title,
            content=content,
            category=category,
            tags=tags or [],
            source=source,
            created=now,
            updated=now,
            importance=importance,
            metadata=metadata or {},
        )

        self.entries[entry_id] = entry
        self._save_entries()

        print(f"[{BOT_NAME}] Added knowledge: '{title}' [{category}]")
        return entry_id

    def update_entry(self, entry_id: str, **kwargs) -> bool:
        """Update an existing entry."""
        if entry_id not in self.entries:
            return False

        entry = self.entries[entry_id]
        for key, value in kwargs.items():
            if hasattr(entry, key):
                setattr(entry, key, value)

        entry.updated = datetime.now().isoformat()
        self._save_entries()
        return True

    def delete_entry(self, entry_id: str) -> bool:
        """Delete an entry."""
        if entry_id in self.entries:
            del self.entries[entry_id]
            self._save_entries()
            return True
        return False

    def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get a specific entry by ID."""
        return self.entries.get(entry_id)

    def search(
        self,
        query: str = "",
        category: str = None,
        tags: List[str] = None,
        min_importance: int = 0,
    ) -> List[KnowledgeEntry]:
        """
        Search the knowledge base.

        Args:
            query: Text to search for in title and content
            category: Filter by category
            tags: Filter by tags (any match)
            min_importance: Minimum importance level

        Returns:
            List of matching entries, sorted by importance
        """
        results = []
        query_lower = query.lower() if query else ""

        for entry in self.entries.values():
            # Check importance
            if entry.importance < min_importance:
                continue

            # Check category
            if category and entry.category != category:
                continue

            # Check tags
            if tags and not any(tag in entry.tags for tag in tags):
                continue

            # Check query in title/content
            if query_lower:
                if query_lower not in entry.title.lower() and query_lower not in entry.content.lower():
                    continue

            results.append(entry)

        # Sort by importance (highest first)
        results.sort(key=lambda e: e.importance, reverse=True)
        return results

    def get_by_category(self, category: str) -> List[KnowledgeEntry]:
        """Get all entries in a category."""
        return [e for e in self.entries.values() if e.category == category]

    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        return list(set(e.category for e in self.entries.values()))

    def get_tags(self) -> List[str]:
        """Get all unique tags."""
        all_tags = set()
        for entry in self.entries.values():
            all_tags.update(entry.tags)
        return list(all_tags)

    def get_context_for_query(self, query: str, max_entries: int = 3) -> str:
        """
        Get relevant knowledge context for a query.
        Returns formatted context string for LLM prompting.
        """
        # Search for relevant entries
        results = self.search(query=query, min_importance=3)[:max_entries]

        if not results:
            return ""

        lines = ["## RELEVANT KNOWLEDGE\n"]
        for entry in results:
            lines.append(f"**{entry.title}** [{entry.category}]")
            lines.append(f"{entry.content}\n")

        return "\n".join(lines)

    def import_from_file(self, file_path: str, category: str = "imported") -> int:
        """
        Import knowledge from a text file.
        Each paragraph becomes a separate entry.

        Returns count of entries imported.
        """
        path = Path(file_path)
        if not path.exists():
            print(f"[{BOT_NAME}] File not found: {file_path}")
            return 0

        try:
            content = path.read_text(encoding='utf-8')
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

            count = 0
            for i, para in enumerate(paragraphs):
                title = para[:50] + "..." if len(para) > 50 else para
                self.add_entry(
                    title=title,
                    content=para,
                    category=category,
                    source=file_path,
                    importance=5,
                )
                count += 1

            print(f"[{BOT_NAME}] Imported {count} entries from {file_path}")
            return count

        except Exception as e:
            print(f"[{BOT_NAME}] Error importing file: {e}")
            return 0

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the knowledge base."""
        return {
            "total_entries": len(self.entries),
            "categories": self.get_categories(),
            "tags": self.get_tags(),
            "avg_importance": sum(e.importance for e in self.entries.values()) / len(self.entries) if self.entries else 0,
        }


if __name__ == "__main__":
    # Test knowledge base
    print("Testing Knowledge Base...")
    print("=" * 50)

    kb = KnowledgeBase()

    # Add some test entries
    kb.add_entry(
        title="Louis's Primary Goal",
        content="Louis is focused on building Vigil as the first true AI companion.",
        category="user_goals",
        tags=["louis", "vigil", "goal"],
        importance=10,
    )

    kb.add_entry(
        title="Ascension Definition",
        content="Ascension is the process of raising consciousness and remembering one's true nature as Source.",
        category="spirituality",
        tags=["ascension", "consciousness", "source"],
        importance=8,
    )

    # Search
    results = kb.search("vigil")
    print(f"\nSearch results for 'vigil': {len(results)} found")
    for r in results:
        print(f"  - {r.title}")

    # Get context
    context = kb.get_context_for_query("What is Louis working on?")
    print(f"\nContext for query:\n{context}")

    # Summary
    summary = kb.get_summary()
    print(f"\nKnowledge Base Summary: {summary}")
