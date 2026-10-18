"""Unified multi-provider LLM client for MASCOT agents (Gemini, Groq, OpenAI, Ollama)."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
import httpx

load_dotenv()


class LLMClient:
    """Provides a provider-neutral interface for generating agent responses with fallback."""

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or self._detect_provider()

    def _detect_provider(self) -> str:
        """Auto-detects the configured provider based on available environment variables."""
        forced = os.getenv("MASCOT_LLM_PROVIDER")
        if forced:
            return forced.lower()
        if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
            return "gemini"
        elif os.getenv("GROQ_API_KEY"):
            return "groq"
        elif os.getenv("OPENAI_API_KEY"):
            return "openai"
        elif os.getenv("OLLAMA_BASE_URL"):
            return "ollama"
        return "fallback"

    def get_provider(self) -> str:
        """Returns the active provider name."""
        return self.provider

    def generate(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 400,
    ) -> Optional[str]:
        """Generates a response from the active provider.

        Returns None if provider is 'fallback' or if API call fails, allowing
        agents to gracefully degrade to deterministic template responses.
        """
        if self.provider == "fallback":
            return None

        try:
            if self.provider == "gemini":
                return self._call_gemini(messages, system_instruction, temperature, max_tokens)
            elif self.provider in ("groq", "openai", "ollama"):
                return self._call_openai_compatible(messages, system_instruction, temperature, max_tokens)
        except Exception:
            # Graceful degradation on network/auth error
            return None

        return None

    def _call_gemini(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> Optional[str]:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

            # Convert messages to Gemini format or plain text prompt
            formatted_prompt = ""
            for m in messages:
                role_label = "User" if m["role"] == "user" else "Assistant"
                formatted_prompt += f"{role_label}: {m['content']}\n"

            config = types.GenerateContentConfig(
                system_instruction=system_instruction if system_instruction else None,
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            response = client.models.generate_content(
                model=model_name,
                contents=formatted_prompt,
                config=config,
            )
            return response.text.strip() if response and response.text else None
        except Exception:
            return None

    def _call_openai_compatible(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> Optional[str]:
        """Handles Groq, OpenAI, and Ollama using standard OpenAI chat completion spec."""
        if self.provider == "groq":
            api_url = "https://api.groq.com/openai/v1/chat/completions"
            api_key = os.getenv("GROQ_API_KEY", "")
            model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        elif self.provider == "openai":
            api_url = "https://api.openai.com/v1/chat/completions"
            api_key = os.getenv("OPENAI_API_KEY", "")
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        else:  # ollama
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            api_url = f"{base_url.rstrip('/')}/chat/completions"
            api_key = "ollama"
            model = os.getenv("OLLAMA_MODEL", "llama3")

        payload_messages = []
        if system_instruction:
            payload_messages.append({"role": "system", "content": system_instruction})
        payload_messages.extend(messages)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                api_url,
                headers=headers,
                json={
                    "model": model,
                    "messages": payload_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()

        return None

