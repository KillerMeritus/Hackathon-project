"""
Abstract base class for LLM providers
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers"""

    def __init__(self, model: str, api_key: str, **kwargs):
        self.model = model
        self.api_key = api_key
        self.max_tokens = kwargs.get('max_tokens', 4096)
        self.temperature = kwargs.get('temperature', 0.7)

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name"""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a response from the LLM

        Args:
            prompt: The main prompt/question
            context: Optional context dictionary with previous outputs
            system_prompt: Optional system prompt to set agent behavior

        Returns:
            Generated text response
        """
        pass

    def _build_messages(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> list:
        """Build message list for chat-based APIs"""
        messages = []

        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add context as part of the user message if provided
        user_content = ""
        if context:
            if context.get("previous_outputs"):
                user_content += "## Previous Agent Outputs:\n"
                for agent_id, output in context["previous_outputs"].items():
                    user_content += f"\n### {agent_id}:\n{output}\n"
                user_content += "\n---\n\n"

            if context.get("query"):
                user_content += f"## Original Query:\n{context['query']}\n\n"

        user_content += f"## Your Task:\n{prompt}"

        messages.append({"role": "user", "content": user_content})

        return messages

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model})"
