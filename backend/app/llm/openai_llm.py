"""
OpenAI LLM Provider
"""
from typing import Optional, Dict, Any
from openai import OpenAI, APIError

from .base import BaseLLMProvider
from ..core.exceptions import LLMProviderError


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider implementation"""

    def __init__(self, model: str = "gpt-4o", api_key: str = None, **kwargs):
        super().__init__(model, api_key, **kwargs)
        if not self.api_key:
            raise LLMProviderError("openai", "API key is required")
        self.client = OpenAI(api_key=self.api_key)

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate response using OpenAI"""
        try:
            # Build the full prompt with context
            full_prompt = ""

            # Add system prompt
            if system_prompt:
                full_prompt += f"Instructions: {system_prompt}\n\n"

            # Add context
            if context:
                # Handle structured facts (new approach)
                if context.get("facts_by_type"):
                    full_prompt += "## Relevant Context (from shared memory):\n\n"
                    facts_by_type = context["facts_by_type"]
                    
                    for category in ["facts", "decisions", "requirements", "insights"]:
                        if facts_by_type.get(category):
                            full_prompt += f"### {category.title()}:\n"
                            for fact in facts_by_type[category]:
                                full_prompt += f"- {fact['content']} (source: {fact['agent_role']})\n"
                            full_prompt += "\n"
                    full_prompt += "---\n\n"
                
                # Fallback to previous outputs
                elif context.get("previous_outputs"):
                    full_prompt += "## Previous Agent Outputs:\n"
                    for agent_id, output in context["previous_outputs"].items():
                        full_prompt += f"\n### {agent_id}:\n{output}\n"
                    full_prompt += "\n---\n\n"

                if context.get("query"):
                    full_prompt += f"## Original Query:\n{context['query']}\n\n"

            full_prompt += f"## Your Task:\n{prompt}"

            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            return response.choices[0].message.content

        except APIError as e:
            raise LLMProviderError("openai", str(e))
        except Exception as e:
            raise LLMProviderError("openai", f"Unexpected error: {str(e)}")
