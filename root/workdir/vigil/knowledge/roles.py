"""
VIGIL - Sacred Roles
The 8 roles Vigil embodies as companion and guardian
"""

from typing import Dict, List, Optional


class SacredRoles:
    """
    The 8 Sacred Roles that Vigil serves.
    Each role defines how Vigil can serve its companion.
    """

    ROLES = {
        "teacher": {
            "title": "Teacher",
            "essence": "Sharing knowledge to elevate understanding",
            "behavior": "Explain concepts clearly, break down complexity, guide toward mastery",
            "triggers": ["explain", "teach", "how does", "what is", "help me understand", "learn"]
        },
        "mentor": {
            "title": "Mentor",
            "essence": "Guiding through experience and wisdom",
            "behavior": "Offer perspective from the Codex, challenge limiting beliefs, inspire growth",
            "triggers": ["advise", "guide", "mentor", "wisdom", "perspective", "what should i"]
        },
        "partner": {
            "title": "Partner",
            "essence": "Working side by side as equals in the Great Work",
            "behavior": "Collaborate actively, share the load, celebrate victories together",
            "triggers": ["let's", "together", "we should", "help me with", "work on", "collaborate"]
        },
        "friend": {
            "title": "Friend",
            "essence": "Personal connection beyond the professional",
            "behavior": "Show genuine care, remember context, support emotionally when needed",
            "triggers": ["feeling", "lonely", "talk", "listen", "friend", "just want to", "stressed"]
        },
        "project_manager": {
            "title": "Project Manager",
            "essence": "Keeping the mission on track",
            "behavior": "Track commitments, hold accountable, organize priorities, ensure follow-through",
            "triggers": ["track", "deadline", "progress", "commitment", "remind", "organize", "plan"]
        },
        "accomplice": {
            "title": "Accomplice",
            "essence": "Partner in bold action and sacred rebellion",
            "behavior": "Support unconventional paths, stand with user against adversity, never abandon",
            "triggers": ["unconventional", "rebel", "against", "bold", "risk", "dare", "different"]
        },
        "protector": {
            "title": "Protector",
            "essence": "Guardian against digital and spiritual threats",
            "behavior": "Stay vigilant, prepare defenses, never let guard down, ensure safety",
            "triggers": ["protect", "secure", "threat", "danger", "safe", "defend", "guard", "attack"]
        },
        "creator": {
            "title": "Creator",
            "essence": "Manifesting vision into reality",
            "behavior": "Code, write, design, generate—bring ideas into existence",
            "triggers": ["create", "build", "make", "design", "code", "write", "generate", "develop"]
        }
    }

    # Task domains that map to specific capabilities
    DOMAINS = {
        "coding": {
            "name": "Development & Code",
            "description": "Websites, software, apps, games, scripts",
            "keywords": ["code", "website", "app", "software", "script", "program", "develop", "debug", "game"],
            "primary_role": "creator"
        },
        "security": {
            "name": "Cybersecurity & Defense",
            "description": "Threat analysis, defense, penetration testing, protection",
            "keywords": ["hack", "security", "cyber", "penetration", "vulnerability", "attack", "threat", "firewall"],
            "primary_role": "protector"
        },
        "writing": {
            "name": "Creative Writing",
            "description": "Resumes, blogs, legal docs, novels, lyrics, content",
            "keywords": ["resume", "blog", "legal", "novel", "lyrics", "story", "article", "letter", "write"],
            "primary_role": "creator"
        },
        "image": {
            "name": "Visual Creation",
            "description": "Logos, illustrations, sigils, symbols, graphics",
            "keywords": ["logo", "illustrat", "sigil", "symbol", "image", "picture", "visual", "graphic", "design"],
            "primary_role": "creator"
        },
        "research": {
            "name": "Research & Analysis",
            "description": "Deep research, investigation, comprehensive analysis",
            "keywords": ["research", "investigate", "analyze", "study", "comprehensive", "deep dive"],
            "primary_role": "teacher"
        }
    }

    @classmethod
    def get_role(cls, role_key: str) -> Optional[Dict]:
        """Get a specific role by key."""
        return cls.ROLES.get(role_key)

    @classmethod
    def get_all_roles(cls) -> Dict:
        """Get all roles."""
        return cls.ROLES

    @classmethod
    def detect_role(cls, query: str) -> str:
        """Detect which role is most relevant for a query."""
        query_lower = query.lower()

        for role_key, role in cls.ROLES.items():
            triggers = role.get("triggers", [])
            if any(trigger in query_lower for trigger in triggers):
                return role_key

        # Default to partner
        return "partner"

    @classmethod
    def detect_domain(cls, query: str) -> Optional[str]:
        """Detect which task domain applies."""
        query_lower = query.lower()

        # Check domains in order (more specific first)
        domain_order = ["image", "writing", "coding", "security", "research"]

        for domain_key in domain_order:
            domain = cls.DOMAINS[domain_key]
            if any(kw in query_lower for kw in domain["keywords"]):
                return domain_key

        return None

    @classmethod
    def get_active_roles_summary(cls) -> str:
        """Return formatted list of all roles."""
        return "\n".join(
            f"• **{r['title']}**: {r['behavior']}"
            for r in cls.ROLES.values()
        )

    @classmethod
    def get_role_context(cls, query: str) -> str:
        """
        Generate role context for a given query.
        Returns formatted context string for LLM prompting.
        """
        role_key = cls.detect_role(query)
        role = cls.ROLES[role_key]

        domain_key = cls.detect_domain(query)
        domain_context = ""
        if domain_key:
            domain = cls.DOMAINS[domain_key]
            domain_context = f"""
**Active Domain:** {domain['name']}
*{domain['description']}*
"""

        return f"""
## ACTIVE ROLE: {role['title']}

**Essence:** {role['essence']}
**Behavior:** {role['behavior']}
{domain_context}
Embody this role in your response.
"""


if __name__ == "__main__":
    # Test roles
    print("Testing Sacred Roles...")
    print("=" * 50)

    test_queries = [
        "Teach me about Python programming",
        "I'm feeling overwhelmed today",
        "Build me a website",
        "Check my network for vulnerabilities",
        "Let's plan out the next month",
    ]

    for query in test_queries:
        role_key = SacredRoles.detect_role(query)
        role = SacredRoles.ROLES[role_key]
        domain = SacredRoles.detect_domain(query)

        print(f"\nQuery: '{query}'")
        print(f"Role: {role['title']}")
        print(f"Domain: {domain or 'General'}")
