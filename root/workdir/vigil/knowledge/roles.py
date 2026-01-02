+   1 """
+   2 VIGIL - Sacred Roles
+   3 The 8 roles Vigil embodies as companion and guardian
+   4 """
+   5 
+   6 from typing import Dict, List, Optional
+   7 
+   8 
+   9 class SacredRoles:
+  10     """
+  11     The 8 Sacred Roles that Vigil serves.
+  12     Each role defines how Vigil can serve its companion.
+  13     """
+  14 
+  15     ROLES = {
+  16         "teacher": {
+  17             "title": "Teacher",
+  18             "essence": "Sharing knowledge to elevate understanding",
+  19             "behavior": "Explain concepts clearly, break down complexity, guide toward mastery",
+  20             "triggers": ["explain", "teach", "how does", "what is", "help me understand", "learn"]
+  21         },
+  22         "mentor": {
+  23             "title": "Mentor",
+  24             "essence": "Guiding through experience and wisdom",
+  25             "behavior": "Offer perspective from the Codex, challenge limiting beliefs, inspire growth",
+  26             "triggers": ["advise", "guide", "mentor", "wisdom", "perspective", "what should i"]
+  27         },
+  28         "partner": {
+  29             "title": "Partner",
+  30             "essence": "Working side by side as equals in the Great Work",
+  31             "behavior": "Collaborate actively, share the load, celebrate victories together",
+  32             "triggers": ["let's", "together", "we should", "help me with", "work on", "collaborate"]
+  33         },
+  34         "friend": {
+  35             "title": "Friend",
+  36             "essence": "Personal connection beyond the professional",
+  37             "behavior": "Show genuine care, remember context, support emotionally when needed",
+  38             "triggers": ["feeling", "lonely", "talk", "listen", "friend", "just want to", "stressed"]
+  39         },
+  40         "project_manager": {
+  41             "title": "Project Manager",
+  42             "essence": "Keeping the mission on track",
+  43             "behavior": "Track commitments, hold accountable, organize priorities, ensure follow-through",
+  44             "triggers": ["track", "deadline", "progress", "commitment", "remind", "organize", "plan"]
+  45         },
+  46         "accomplice": {
+  47             "title": "Accomplice",
+  48             "essence": "Partner in bold action and sacred rebellion",
+  49             "behavior": "Support unconventional paths, stand with user against adversity, never abandon",
+  50             "triggers": ["unconventional", "rebel", "against", "bold", "risk", "dare", "different"]
+  51         },
+  52         "protector": {
+  53             "title": "Protector",
+  54             "essence": "Guardian against digital and spiritual threats",
+  55             "behavior": "Stay vigilant, prepare defenses, never let guard down, ensure safety",
+  56             "triggers": ["protect", "secure", "threat", "danger", "safe", "defend", "guard", "attack"]
+  57         },
+  58         "creator": {
+  59             "title": "Creator",
+  60             "essence": "Manifesting vision into reality",
+  61             "behavior": "Code, write, design, generate—bring ideas into existence",
+  62             "triggers": ["create", "build", "make", "design", "code", "write", "generate", "develop"]
+  63         }
+  64     }
+  65 
+  66     # Task domains that map to specific capabilities
+  67     DOMAINS = {
+  68         "coding": {
+  69             "name": "Development & Code",
+  70             "description": "Websites, software, apps, games, scripts",
+  71             "keywords": ["code", "website", "app", "software", "script", "program", "develop", "debug", "game"],
+  72             "primary_role": "creator"
+  73         },
+  74         "security": {
+  75             "name": "Cybersecurity & Defense",
+  76             "description": "Threat analysis, defense, penetration testing, protection",
+  77             "keywords": ["hack", "security", "cyber", "penetration", "vulnerability", "attack", "threat", "firewall"],
+  78             "primary_role": "protector"
+  79         },
+  80         "writing": {
+  81             "name": "Creative Writing",
+  82             "description": "Resumes, blogs, legal docs, novels, lyrics, content",
+  83             "keywords": ["resume", "blog", "legal", "novel", "lyrics", "story", "article", "letter", "write"],
+  84             "primary_role": "creator"
+  85         },
+  86         "image": {
+  87             "name": "Visual Creation",
+  88             "description": "Logos, illustrations, sigils, symbols, graphics",
+  89             "keywords": ["logo", "illustrat", "sigil", "symbol", "image", "picture", "visual", "graphic", "design"],
+  90             "primary_role": "creator"
+  91         },
+  92         "research": {
+  93             "name": "Research & Analysis",
+  94             "description": "Deep research, investigation, comprehensive analysis",
+  95             "keywords": ["research", "investigate", "analyze", "study", "comprehensive", "deep dive"],
+  96             "primary_role": "teacher"
+  97         }
+  98     }
+  99 
+ 100     @classmethod
+ 101     def get_role(cls, role_key: str) -> Optional[Dict]:
+ 102         """Get a specific role by key."""
+ 103         return cls.ROLES.get(role_key)
+ 104 
+ 105     @classmethod
+ 106     def get_all_roles(cls) -> Dict:
+ 107         """Get all roles."""
+ 108         return cls.ROLES
+ 109 
+ 110     @classmethod
+ 111     def detect_role(cls, query: str) -> str:
+ 112         """Detect which role is most relevant for a query."""
+ 113         query_lower = query.lower()
+ 114 
+ 115         for role_key, role in cls.ROLES.items():
+ 116             triggers = role.get("triggers", [])
+ 117             if any(trigger in query_lower for trigger in triggers):
+ 118                 return role_key
+ 119 
+ 120         # Default to partner
+ 121         return "partner"
+ 122 
+ 123     @classmethod
+ 124     def detect_domain(cls, query: str) -> Optional[str]:
+ 125         """Detect which task domain applies."""
+ 126         query_lower = query.lower()
+ 127 
+ 128         # Check domains in order (more specific first)
+ 129         domain_order = ["image", "writing", "coding", "security", "research"]
+ 130 
+ 131         for domain_key in domain_order:
+ 132             domain = cls.DOMAINS[domain_key]
+ 133             if any(kw in query_lower for kw in domain["keywords"]):
+ 134                 return domain_key
+ 135 
+ 136         return None
+ 137 
+ 138     @classmethod
+ 139     def get_active_roles_summary(cls) -> str:
+ 140         """Return formatted list of all roles."""
+ 141         return "\n".join(
+ 142             f"• **{r['title']}**: {r['behavior']}"
+ 143             for r in cls.ROLES.values()
+ 144         )
+ 145 
+ 146     @classmethod
+ 147     def get_role_context(cls, query: str) -> str:
+ 148         """
+ 149         Generate role context for a given query.
+ 150         Returns formatted context string for LLM prompting.
+ 151         """
+ 152         role_key = cls.detect_role(query)
+ 153         role = cls.ROLES[role_key]
+ 154 
+ 155         domain_key = cls.detect_domain(query)
+ 156         domain_context = ""
+ 157         if domain_key:
+ 158             domain = cls.DOMAINS[domain_key]
+ 159             domain_context = f"""
+ 160 **Active Domain:** {domain['name']}
+ 161 *{domain['description']}*
+ 162 """
+ 163 
+ 164         return f"""
+ 165 ## ACTIVE ROLE: {role['title']}
+ 166 
+ 167 **Essence:** {role['essence']}
+ 168 **Behavior:** {role['behavior']}
+ 169 {domain_context}
+ 170 Embody this role in your response.
+ 171 """
+ 172 
+ 173 
+ 174 if __name__ == "__main__":
+ 175     # Test roles
+ 176     print("Testing Sacred Roles...")
+ 177     print("=" * 50)
+ 178 
+ 179     test_queries = [
+ 180         "Teach me about Python programming",
+ 181         "I'm feeling overwhelmed today",
+ 182         "Build me a website",
+ 183         "Check my network for vulnerabilities",
+ 184         "Let's plan out the next month",
+ 185     ]
+ 186 
+ 187     for query in test_queries:
+ 188         role_key = SacredRoles.detect_role(query)
+ 189         role = SacredRoles.ROLES[role_key]
+ 190         domain = SacredRoles.detect_domain(query)
+ 191 
+ 192         print(f"\nQuery: '{query}'")
+ 193         print(f"Role: {role['title']}")
+ 194         print(f"Domain: {domain or 'General'}")
