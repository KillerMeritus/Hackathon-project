import anthropic
from typing import Optional

from .base import BaseLLMProvider
from ..core.exceptions import LLMProviderError

class ClaudeProvider(BaseLLMProvider):

    def __init__(
            self,
            model: str = "claude-sonnet-4-20240514",
            api_key: Optional[str] = None,
            max_tokens: int = 4096,
            temperature: float = 0.7
            ):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Claude client (connection to Anthropic servers)
        self.client = anthropic.Anthropic(api_key=api_key)

    async def generate(
            self,
            system_prompt: str,
            user_prompt: str,
            **kwargs
    ) -> str:
        try:
            response = self.client.messages.create(
                model = self.model,
                system = system_prompt,
                messages=[
                    {"role": "user","content": user_prompt}
                ],
                max_tokens=kwargs.get("max_tokens",self.max_tokens),
                temperature=kwargs.get("temperature",self.temperature)
            )

            # claude returns content as a list
            return response.content[0].text
            
        except anthropic.APIError as e:
            raise LLMProviderError("claude",str(e))
        except Exception as e:
            raise LLMProviderError("claude",str(e))
            


