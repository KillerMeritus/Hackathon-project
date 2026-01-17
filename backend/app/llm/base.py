from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseLLMProvider(ABC):
    """
    Base abstraction for all LLM providers.
    Any concrete LLM (OpenAI, Claude, Gemini) must follow this contract.
    """

    def __init__(self, model: str, api_key: str, **kwargs):
        self.model = model
        self.api_key = api_key
        self.max_tokens = kwargs.get("max_tokens", 4096)
        self.temperature = kwargs.get("temperature", 0.7)

    def _build_messages(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> list:
        """
        Builds chat-style messages for LLMs.
        System message defines behavior.
        User message contains context + task.
        """
        messages = []

        # System prompt (agent behavior)
        if system_prompt:
            messages.append(
                {"role": "system", "content": system_prompt}
            )

        user_content = ""

        # Previous agent outputs (context)
        if context:
            if context.get("previous_outputs"):
                user_content += "## Previous Agent Outputs:\n"
                for agent_id, output in context["previous_outputs"].items():
                    user_content += f"\n### {agent_id}:\n{output}\n"
                user_content += "\n---\n\n"

            if context.get("query"):
                user_content += f"## Original Query:\n{context['query']}\n\n"

        # Current task (always last)
        user_content += f"## Your Task:\n{prompt}"

        messages.append(
            {"role": "user", "content": user_content}
        )

        return messages

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a response from the LLM.
        Must be implemented by concrete providers.
        """
        pass
