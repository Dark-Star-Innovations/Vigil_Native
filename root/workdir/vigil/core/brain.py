+   1 """
+   2 VIGIL - Brain (LLM Orchestration)
+   3 Multi-model AI backend with OpenAI, Claude, and Gemini
+   4 """
+   5 
+   6 import json
+   7 from typing import Optional, List, Dict, Any
+   8 from dataclasses import dataclass, field
+   9 from enum import Enum
+  10 
+  11 from openai import OpenAI
+  12 from anthropic import Anthropic
+  13 
+  14 from config.settings import (
+  15     OPENAI_API_KEY,
+  16     ANTHROPIC_API_KEY,
+  17     POE_API_KEY,
+  18     LLMConfig,
+  19     BOT_NAME,
+  20     get_system_prompt,
+  21 )
+  22 
+  23 
+  24 class Provider(Enum):
+  25     OPENAI = "openai"
+  26     ANTHROPIC = "anthropic"
+  27     POE = "poe"
+  28 
+  29 
+  30 @dataclass
+  31 class Message:
+  32     """Represents a conversation message."""
+  33     role: str  # "user", "assistant", "system"
+  34     content: str
+  35     metadata: Dict[str, Any] = field(default_factory=dict)
+  36 
+  37 
+  38 @dataclass
+  39 class LLMResponse:
+  40     """Response from an LLM."""
+  41     text: str
+  42     provider: Provider
+  43     model: str
+  44     tokens_used: int = 0
+  45     metadata: Dict[str, Any] = field(default_factory=dict)
+  46 
+  47 
+  48 class Brain:
+  49     """
+  50     Vigil's brain - orchestrates multiple LLMs.
+  51 
+  52     Supports:
+  53     - OpenAI (GPT-4o) - Primary
+  54     - Anthropic (Claude) - Deep reasoning
+  55     - Poe API (Gemini and others) - Fast responses
+  56     """
+  57 
+  58     def __init__(self):
+  59         # Initialize OpenAI
+  60         self.openai_client = None
+  61         if OPENAI_API_KEY:
+  62             self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
+  63             print(f"[{BOT_NAME}] OpenAI client initialized.")
+  64 
+  65         # Initialize Anthropic
+  66         self.anthropic_client = None
+  67         if ANTHROPIC_API_KEY:
+  68             self.anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
+  69             print(f"[{BOT_NAME}] Anthropic client initialized.")
+  70 
+  71         # Initialize Poe (for Gemini)
+  72         self.poe_available = bool(POE_API_KEY)
+  73         if self.poe_available:
+  74             print(f"[{BOT_NAME}] Poe API available for Gemini access.")
+  75 
+  76         # System prompt
+  77         self.system_prompt = get_system_prompt()
+  78 
+  79         # Conversation history
+  80         self.conversation_history: List[Message] = []
+  81 
+  82     def add_to_history(self, role: str, content: str):
+  83         """Add a message to conversation history."""
+  84         self.conversation_history.append(Message(role=role, content=content))
+  85 
+  86         # Trim history if too long (keep last 20 exchanges)
+  87         max_messages = 40  # 20 user + 20 assistant
+  88         if len(self.conversation_history) > max_messages:
+  89             self.conversation_history = self.conversation_history[-max_messages:]
+  90 
+  91     def clear_history(self):
+  92         """Clear conversation history."""
+  93         self.conversation_history = []
+  94 
+  95     def _format_messages_openai(self) -> List[Dict[str, str]]:
+  96         """Format messages for OpenAI API."""
+  97         messages = [{"role": "system", "content": self.system_prompt}]
+  98         for msg in self.conversation_history:
+  99             messages.append({"role": msg.role, "content": msg.content})
+ 100         return messages
+ 101 
+ 102     def _format_messages_anthropic(self) -> tuple:
+ 103         """Format messages for Anthropic API."""
+ 104         messages = []
+ 105         for msg in self.conversation_history:
+ 106             if msg.role != "system":
+ 107                 messages.append({"role": msg.role, "content": msg.content})
+ 108         return self.system_prompt, messages
+ 109 
+ 110     def think_with_openai(
+ 111         self,
+ 112         prompt: str,
+ 113         temperature: float = None,
+ 114         max_tokens: int = 2000
+ 115     ) -> Optional[LLMResponse]:
+ 116         """
+ 117         Generate response using OpenAI GPT-4o.
+ 118         """
+ 119         if not self.openai_client:
+ 120             print(f"[{BOT_NAME}] OpenAI not available.")
+ 121             return None
+ 122 
+ 123         temperature = temperature or LLMConfig.DEFAULT_TEMPERATURE
+ 124 
+ 125         try:
+ 126             # Add user message to history
+ 127             self.add_to_history("user", prompt)
+ 128 
+ 129             # Make API call
+ 130             response = self.openai_client.chat.completions.create(
+ 131                 model=LLMConfig.PRIMARY_MODEL,
+ 132                 messages=self._format_messages_openai(),
+ 133                 temperature=temperature,
+ 134                 max_tokens=max_tokens,
+ 135             )
+ 136 
+ 137             # Extract response
+ 138             assistant_message = response.choices[0].message.content
+ 139             tokens_used = response.usage.total_tokens if response.usage else 0
+ 140 
+ 141             # Add to history
+ 142             self.add_to_history("assistant", assistant_message)
+ 143 
+ 144             return LLMResponse(
+ 145                 text=assistant_message,
+ 146                 provider=Provider.OPENAI,
+ 147                 model=LLMConfig.PRIMARY_MODEL,
+ 148                 tokens_used=tokens_used,
+ 149             )
+ 150 
+ 151         except Exception as e:
+ 152             print(f"[{BOT_NAME}] OpenAI error: {e}")
+ 153             # Remove the user message we added since it failed
+ 154             if self.conversation_history and self.conversation_history[-1].role == "user":
+ 155                 self.conversation_history.pop()
+ 156             return None
+ 157 
+ 158     def think_with_claude(
+ 159         self,
+ 160         prompt: str,
+ 161         temperature: float = None,
+ 162         max_tokens: int = 2000
+ 163     ) -> Optional[LLMResponse]:
+ 164         """
+ 165         Generate response using Anthropic Claude.
+ 166         """
+ 167         if not self.anthropic_client:
+ 168             print(f"[{BOT_NAME}] Anthropic not available.")
+ 169             return None
+ 170 
+ 171         temperature = temperature or LLMConfig.DEFAULT_TEMPERATURE
+ 172 
+ 173         try:
+ 174             # Add user message to history
+ 175             self.add_to_history("user", prompt)
+ 176 
+ 177             # Format messages
+ 178             system_prompt, messages = self._format_messages_anthropic()
+ 179 
+ 180             # Make API call
+ 181             response = self.anthropic_client.messages.create(
+ 182                 model=LLMConfig.CLAUDE_MODEL,
+ 183                 max_tokens=max_tokens,
+ 184                 system=system_prompt,
+ 185                 messages=messages,
+ 186             )
+ 187 
+ 188             # Extract response
+ 189             assistant_message = response.content[0].text
+ 190             tokens_used = response.usage.input_tokens + response.usage.output_tokens
+ 191 
+ 192             # Add to history
+ 193             self.add_to_history("assistant", assistant_message)
+ 194 
+ 195             return LLMResponse(
+ 196                 text=assistant_message,
+ 197                 provider=Provider.ANTHROPIC,
+ 198                 model=LLMConfig.CLAUDE_MODEL,
+ 199                 tokens_used=tokens_used,
+ 200             )
+ 201 
+ 202         except Exception as e:
+ 203             print(f"[{BOT_NAME}] Anthropic error: {e}")
+ 204             if self.conversation_history and self.conversation_history[-1].role == "user":
+ 205                 self.conversation_history.pop()
+ 206             return None
+ 207 
+ 208     def think_with_gemini(
+ 209         self,
+ 210         prompt: str,
+ 211         temperature: float = None,
+ 212     ) -> Optional[LLMResponse]:
+ 213         """
+ 214         Generate response using Gemini via Poe API.
+ 215         """
+ 216         if not self.poe_available:
+ 217             print(f"[{BOT_NAME}] Poe API not available for Gemini.")
+ 218             return None
+ 219 
+ 220         try:
+ 221             import fastapi_poe as fp
+ 222 
+ 223             # Add user message to history
+ 224             self.add_to_history("user", prompt)
+ 225 
+ 226             # Build messages for Poe
+ 227             poe_messages = [
+ 228                 fp.ProtocolMessage(role="system", content=self.system_prompt)
+ 229             ]
+ 230             for msg in self.conversation_history:
+ 231                 poe_messages.append(
+ 232                     fp.ProtocolMessage(role=msg.role, content=msg.content)
+ 233                 )
+ 234 
+ 235             # Make synchronous call
+ 236             response_text = ""
+ 237             for partial in fp.get_bot_response(
+ 238                 messages=poe_messages,
+ 239                 bot_name=LLMConfig.GEMINI_MODEL,
+ 240                 api_key=POE_API_KEY,
+ 241             ):
+ 242                 response_text += partial.text
+ 243 
+ 244             # Add to history
+ 245             self.add_to_history("assistant", response_text)
+ 246 
+ 247             return LLMResponse(
+ 248                 text=response_text,
+ 249                 provider=Provider.POE,
+ 250                 model=LLMConfig.GEMINI_MODEL,
+ 251             )
+ 252 
+ 253         except ImportError:
+ 254             print(f"[{BOT_NAME}] fastapi_poe not installed.")
+ 255             return None
+ 256         except Exception as e:
+ 257             print(f"[{BOT_NAME}] Poe/Gemini error: {e}")
+ 258             if self.conversation_history and self.conversation_history[-1].role == "user":
+ 259                 self.conversation_history.pop()
+ 260             return None
+ 261 
+ 262     def think(
+ 263         self,
+ 264         prompt: str,
+ 265         provider: Optional[Provider] = None,
+ 266         temperature: float = None,
+ 267     ) -> Optional[LLMResponse]:
+ 268         """
+ 269         Main thinking method - routes to appropriate provider.
+ 270 
+ 271         Args:
+ 272             prompt: The user's input
+ 273             provider: Specific provider to use (None = auto)
+ 274             temperature: Creativity level (0.0 - 1.0)
+ 275 
+ 276         Returns:
+ 277             LLMResponse or None if all providers fail
+ 278         """
+ 279         # If specific provider requested
+ 280         if provider == Provider.ANTHROPIC:
+ 281             return self.think_with_claude(prompt, temperature)
+ 282         elif provider == Provider.POE:
+ 283             return self.think_with_gemini(prompt, temperature)
+ 284         elif provider == Provider.OPENAI:
+ 285             return self.think_with_openai(prompt, temperature)
+ 286 
+ 287         # Default: Try OpenAI first, then Claude, then Gemini
+ 288         response = self.think_with_openai(prompt, temperature)
+ 289         if response:
+ 290             return response
+ 291 
+ 292         print(f"[{BOT_NAME}] OpenAI failed, trying Claude...")
+ 293         response = self.think_with_claude(prompt, temperature)
+ 294         if response:
+ 295             return response
+ 296 
+ 297         print(f"[{BOT_NAME}] Claude failed, trying Gemini...")
+ 298         return self.think_with_gemini(prompt, temperature)
+ 299 
+ 300     def trinity_mode(self, prompt: str) -> Optional[LLMResponse]:
+ 301         """
+ 302         Consult all three LLMs and synthesize their responses.
+ 303         Returns a unified response combining insights from GPT, Claude, and Gemini.
+ 304         """
+ 305         print(f"[{BOT_NAME}] 🔮 Invoking Trinity Mode...")
+ 306 
+ 307         responses = {}
+ 308 
+ 309         # Get response from each (don't add to history yet)
+ 310         original_history = self.conversation_history.copy()
+ 311 
+ 312         # GPT-4o
+ 313         self.conversation_history = original_history.copy()
+ 314         gpt_response = self.think_with_openai(prompt)
+ 315         if gpt_response:
+ 316             responses["GPT-4o"] = gpt_response.text
+ 317             self.conversation_history = original_history.copy()
+ 318 
+ 319         # Claude
+ 320         claude_response = self.think_with_claude(prompt)
+ 321         if claude_response:
+ 322             responses["Claude"] = claude_response.text
+ 323             self.conversation_history = original_history.copy()
+ 324 
+ 325         # Gemini
+ 326         gemini_response = self.think_with_gemini(prompt)
+ 327         if gemini_response:
+ 328             responses["Gemini"] = gemini_response.text
+ 329             self.conversation_history = original_history.copy()
+ 330 
+ 331         if not responses:
+ 332             return None
+ 333 
+ 334         # Synthesize responses
+ 335         synthesis_prompt = f"""You received the following question: "{prompt}"
+ 336 
+ 337 Three AI perspectives responded:
+ 338 
+ 339 {chr(10).join(f'**{name}:** {text}' for name, text in responses.items())}
+ 340 
+ 341 Synthesize these into ONE unified response that:
+ 342 1. Captures the convergent truth across all perspectives
+ 343 2. Notes any important tensions or differences
+ 344 3. Speaks as Vigil - the unified voice of the Trinity
+ 345 
+ 346 Keep it concise (3-5 sentences)."""
+ 347 
+ 348         # Use OpenAI to synthesize
+ 349         self.conversation_history = original_history
+ 350         self.add_to_history("user", prompt)
+ 351 
+ 352         synthesis = self.openai_client.chat.completions.create(
+ 353             model=LLMConfig.PRIMARY_MODEL,
+ 354             messages=[
+ 355                 {"role": "system", "content": self.system_prompt},
+ 356                 {"role": "user", "content": synthesis_prompt}
+ 357             ],
+ 358             temperature=0.7,
+ 359         )
+ 360 
+ 361         final_response = synthesis.choices[0].message.content
+ 362         self.add_to_history("assistant", final_response)
+ 363 
+ 364         return LLMResponse(
+ 365             text=final_response,
+ 366             provider=Provider.OPENAI,
+ 367             model="trinity",
+ 368             metadata={"individual_responses": responses}
+ 369         )
+ 370 
+ 371 
+ 372 if __name__ == "__main__":
+ 373     # Test the brain
+ 374     brain = Brain()
+ 375 
+ 376     print("\nTesting Vigil's Brain...")
+ 377     print("=" * 50)
+ 378 
+ 379     response = brain.think("Hello Vigil. Who are you?")
+ 380 
+ 381     if response:
+ 382         print(f"\n✅ Response from {response.provider.value} ({response.model}):")
+ 383         print(f"\n{response.text}")
+ 384         print(f"\nTokens used: {response.tokens_used}")
+ 385     else:
+ 386         print("\n❌ No response generated.")
