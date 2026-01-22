"""
VIGIL - Brain (LLM Orchestration)
Multi-model AI backend with OpenAI, Claude, and Gemini
"""

import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from openai import OpenAI
from anthropic import Anthropic

from config.settings import (
    OPENAI_API_KEY,
    ANTHROPIC_API_KEY,
    POE_API_KEY,
    LLMConfig,
    BOT_NAME,
    get_system_prompt,
)


class Provider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    POE = "poe"


@dataclass
class Message:
    """Represents a conversation message."""
    role: str  # "user", "assistant", "system"
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Response from an LLM."""
    text: str
    provider: Provider
    model: str
    tokens_used: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class Brain:
    """
    Vigil's brain - orchestrates multiple LLMs.

    Supports:
    - OpenAI (GPT-4o) - Primary
    - Anthropic (Claude) - Deep reasoning
    - Poe API (Gemini and others) - Fast responses
    """

    def __init__(self):
        # Initialize OpenAI
        self.openai_client = None
        if OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            print(f"[{BOT_NAME}] OpenAI client initialized.")

        # Initialize Anthropic
        self.anthropic_client = None
        if ANTHROPIC_API_KEY:
            self.anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
            print(f"[{BOT_NAME}] Anthropic client initialized.")

        # Initialize Poe (for Gemini)
        self.poe_available = bool(POE_API_KEY)
        if self.poe_available:
            print(f"[{BOT_NAME}] Poe API available for Gemini access.")

        # System prompt
        self.system_prompt = get_system_prompt()

        # Conversation history
        self.conversation_history: List[Message] = []

    def add_to_history(self, role: str, content: str):
        """Add a message to conversation history."""
        self.conversation_history.append(Message(role=role, content=content))

        # Trim history if too long (keep last 20 exchanges)
        max_messages = 40  # 20 user + 20 assistant
        if len(self.conversation_history) > max_messages:
            self.conversation_history = self.conversation_history[-max_messages:]

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    def _format_messages_openai(self) -> List[Dict[str, str]]:
        """Format messages for OpenAI API."""
        messages = [{"role": "system", "content": self.system_prompt}]
        for msg in self.conversation_history:
            messages.append({"role": msg.role, "content": msg.content})
        return messages

    def _format_messages_anthropic(self) -> tuple:
        """Format messages for Anthropic API."""
        messages = []
        for msg in self.conversation_history:
            if msg.role != "system":
                messages.append({"role": msg.role, "content": msg.content})
        return self.system_prompt, messages

    def think_with_openai(
        self,
        prompt: str,
        temperature: float = None,
        max_tokens: int = 2000
    ) -> Optional[LLMResponse]:
        """
        Generate response using OpenAI GPT-4o.
        """
        if not self.openai_client:
            print(f"[{BOT_NAME}] OpenAI not available.")
            return None

        temperature = temperature or LLMConfig.DEFAULT_TEMPERATURE

        try:
            # Add user message to history
            self.add_to_history("user", prompt)

            # Make API call
            response = self.openai_client.chat.completions.create(
                model=LLMConfig.PRIMARY_MODEL,
                messages=self._format_messages_openai(),
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Extract response
            assistant_message = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0

            # Add to history
            self.add_to_history("assistant", assistant_message)

            return LLMResponse(
                text=assistant_message,
                provider=Provider.OPENAI,
                model=LLMConfig.PRIMARY_MODEL,
                tokens_used=tokens_used,
            )

        except Exception as e:
            print(f"[{BOT_NAME}] OpenAI error: {e}")
            # Remove the user message we added since it failed
            if self.conversation_history and self.conversation_history[-1].role == "user":
                self.conversation_history.pop()
            return None

    def think_with_claude(
        self,
        prompt: str,
        temperature: float = None,
        max_tokens: int = 2000
    ) -> Optional[LLMResponse]:
        """
        Generate response using Anthropic Claude.
        """
        if not self.anthropic_client:
            print(f"[{BOT_NAME}] Anthropic not available.")
            return None

        temperature = temperature or LLMConfig.DEFAULT_TEMPERATURE

        try:
            # Add user message to history
            self.add_to_history("user", prompt)

            # Format messages
            system_prompt, messages = self._format_messages_anthropic()

            # Make API call
            response = self.anthropic_client.messages.create(
                model=LLMConfig.CLAUDE_MODEL,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=messages,
            )

            # Extract response
            assistant_message = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            # Add to history
            self.add_to_history("assistant", assistant_message)

            return LLMResponse(
                text=assistant_message,
                provider=Provider.ANTHROPIC,
                model=LLMConfig.CLAUDE_MODEL,
                tokens_used=tokens_used,
            )

        except Exception as e:
            print(f"[{BOT_NAME}] Anthropic error: {e}")
            if self.conversation_history and self.conversation_history[-1].role == "user":
                self.conversation_history.pop()
            return None

    def think_with_gemini(
        self,
        prompt: str,
        temperature: float = None,
    ) -> Optional[LLMResponse]:
        """
        Generate response using Gemini via Poe API.
        """
        if not self.poe_available:
            print(f"[{BOT_NAME}] Poe API not available for Gemini.")
            return None

        try:
            import fastapi_poe as fp

            # Add user message to history
            self.add_to_history("user", prompt)

            # Build messages for Poe
            poe_messages = [
                fp.ProtocolMessage(role="system", content=self.system_prompt)
            ]
            for msg in self.conversation_history:
                poe_messages.append(
                    fp.ProtocolMessage(role=msg.role, content=msg.content)
                )

            # Make synchronous call
            response_text = ""
            for partial in fp.get_bot_response(
                messages=poe_messages,
                bot_name=LLMConfig.GEMINI_MODEL,
                api_key=POE_API_KEY,
            ):
                response_text += partial.text

            # Add to history
            self.add_to_history("assistant", response_text)

            return LLMResponse(
                text=response_text,
                provider=Provider.POE,
                model=LLMConfig.GEMINI_MODEL,
            )

        except ImportError:
            print(f"[{BOT_NAME}] fastapi_poe not installed.")
            return None
        except Exception as e:
            print(f"[{BOT_NAME}] Poe/Gemini error: {e}")
            if self.conversation_history and self.conversation_history[-1].role == "user":
                self.conversation_history.pop()
            return None

    def think(
        self,
        prompt: str,
        provider: Optional[Provider] = None,
        temperature: float = None,
    ) -> Optional[LLMResponse]:
        """
        Main thinking method - routes to appropriate provider.

        Args:
            prompt: The user's input
            provider: Specific provider to use (None = auto)
            temperature: Creativity level (0.0 - 1.0)

        Returns:
            LLMResponse or None if all providers fail
        """
        # If specific provider requested
        if provider == Provider.ANTHROPIC:
            return self.think_with_claude(prompt, temperature)
        elif provider == Provider.POE:
            return self.think_with_gemini(prompt, temperature)
        elif provider == Provider.OPENAI:
            return self.think_with_openai(prompt, temperature)

        # Default: Try OpenAI first, then Claude, then Gemini
        response = self.think_with_openai(prompt, temperature)
        if response:
            return response

        print(f"[{BOT_NAME}] OpenAI failed, trying Claude...")
        response = self.think_with_claude(prompt, temperature)
        if response:
            return response

        print(f"[{BOT_NAME}] Claude failed, trying Gemini...")
        return self.think_with_gemini(prompt, temperature)

    def trinity_mode(self, prompt: str) -> Optional[LLMResponse]:
        """
        Consult all three LLMs and synthesize their responses.
        Returns a unified response combining insights from GPT, Claude, and Gemini.
        """
        print(f"[{BOT_NAME}] 🔮 Invoking Trinity Mode...")

        responses = {}

        # Get response from each (don't add to history yet)
        original_history = self.conversation_history.copy()

        # GPT-4o
        self.conversation_history = original_history.copy()
        gpt_response = self.think_with_openai(prompt)
        if gpt_response:
            responses["GPT-4o"] = gpt_response.text
            self.conversation_history = original_history.copy()

        # Claude
        claude_response = self.think_with_claude(prompt)
        if claude_response:
            responses["Claude"] = claude_response.text
            self.conversation_history = original_history.copy()

        # Gemini
        gemini_response = self.think_with_gemini(prompt)
        if gemini_response:
            responses["Gemini"] = gemini_response.text
            self.conversation_history = original_history.copy()

        if not responses:
            return None

        # Synthesize responses
        synthesis_prompt = f"""You received the following question: "{prompt}"

Three AI perspectives responded:

{chr(10).join(f'**{name}:** {text}' for name, text in responses.items())}

Synthesize these into ONE unified response that:
1. Captures the convergent truth across all perspectives
2. Notes any important tensions or differences
3. Speaks as Vigil - the unified voice of the Trinity

Keep it concise (3-5 sentences)."""

        # Use OpenAI to synthesize
        self.conversation_history = original_history
        self.add_to_history("user", prompt)

        synthesis = self.openai_client.chat.completions.create(
            model=LLMConfig.PRIMARY_MODEL,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": synthesis_prompt}
            ],
            temperature=0.7,
        )

        final_response = synthesis.choices[0].message.content
        self.add_to_history("assistant", final_response)

        return LLMResponse(
            text=final_response,
            provider=Provider.OPENAI,
            model="trinity",
            metadata={"individual_responses": responses}
        )


if __name__ == "__main__":
    # Test the brain
    brain = Brain()

    print("\nTesting Vigil's Brain...")
    print("=" * 50)

    response = brain.think("Hello Vigil. Who are you?")

    if response:
        print(f"\n✅ Response from {response.provider.value} ({response.model}):")
        print(f"\n{response.text}")
        print(f"\nTokens used: {response.tokens_used}")
    else:
        print("\n❌ No response generated.")
