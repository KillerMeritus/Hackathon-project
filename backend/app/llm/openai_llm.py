"""
OpenAI LLM Provider - GPT models
"""
import openai
from typing import Optional

from .base import BaseLLMProvider
from ..core.exceptions import LLMProviderError


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API provider.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # OpenAI client (connection to OpenAI servers)
        self.client = openai.OpenAI(api_key=api_key)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> str:
        try:
            # Build chat messages
            messages = self._build_messages(system_prompt, user_prompt)

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature)
            )

            # Return text output
            return response.choices[0].message.content

        except openai.APIError as e:
            raise LLMProviderError("openai", str(e))
        except Exception as e:
            raise LLMProviderError("openai", str(e))
