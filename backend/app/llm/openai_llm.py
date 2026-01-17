from typing import Optional, Dict, Any

from openai import OpenAI, APIError

from .base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """
    Concrete OpenAI implementation of BaseLLMProvider.
    """

    def __init__(self, model: str, api_key: str, **kwargs):
        super().__init__(model, api_key, **kwargs)

        if not api_key:
            raise ValueError("OpenAI API key is required")

        self.client = OpenAI(api_key=self.api_key)

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        try:
            messages = self._build_messages(
                prompt=prompt,
                context=context,
                system_prompt=system_prompt
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            if response.choices:
                return response.choices[0].message.content or ""

            return ""

        except APIError as e:
            raise RuntimeError(f"OpenAI API error: {e}")

        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}")
