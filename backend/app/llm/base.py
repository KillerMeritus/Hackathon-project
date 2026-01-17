"""
Base LLM Provider - Abstract class for all AI providers
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.

    Any LLM (OpenAI, Claude, Gemini) must implement `generate`.
    """

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> str:
        """
        Generate a response from the LLM.

        system_prompt -> defines behavior
        user_prompt   -> actual task
        """
        pass

    def _build_messages(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> List[Dict[str, str]]:
        """
        Build messages in chat format used by most LLMs.
        """
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        messages.append({
            "role": "user",
            "content": user_prompt
        })

        return messages
