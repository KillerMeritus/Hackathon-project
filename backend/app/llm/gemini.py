"""
Gemini LLM Provider - Google Gemini models
"""
import google.generativeai as genai
from typing import Optional

from .base import BaseLLMProvider
from ..core.exceptions import LLMProviderError


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini API provider.
    """

    def __init__(
        self,
        model: str = "gemini-1.5-flash",
        api_key: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        self.model_name = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Configure Gemini API key
        genai.configure(api_key=api_key)

        # Create Gemini model
        self.model = genai.GenerativeModel(model)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> str:
        try:
            # Gemini does not support system role, so we combine prompts
            full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"

            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=kwargs.get("max_tokens", self.max_tokens),
                    temperature=kwargs.get("temperature", self.temperature)
                )
            )

            return response.text

        except Exception as e:
            raise LLMProviderError("gemini", str(e))
