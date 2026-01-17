"""
Anthropic Claude LLM Provider
"""
from typing import Optional, Dict, Any
import anthropic

from .base import BaseLLMProvider
from ..core.exceptions import LLMProviderError


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude provider implementation"""

    def __init__(self, model: str = "claude-sonnet-4-20250514", api_key: str = None, **kwargs):
        super().__init__(model, api_key, **kwargs)
        if not self.api_key:
            raise LLMProviderError("anthropic", "API key is required")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate response using Claude"""
        try:
            # Build the user message with context
            user_content = ""
            if context:
                # Handle structured facts (new approach)
                if context.get("facts_by_type"):
                    user_content += "## Relevant Context (from shared memory):\n\n"
                    facts_by_type = context["facts_by_type"]
                    
                    for category in ["facts", "decisions", "requirements", "insights"]:
                        if facts_by_type.get(category):
                            user_content += f"### {category.title()}:\n"
                            for fact in facts_by_type[category]:
                                user_content += f"- {fact['content']} (source: {fact['agent_role']})\n"
                            user_content += "\n"
                    user_content += "---\n\n"
                
                # Fallback to previous outputs
                elif context.get("previous_outputs"):
                    user_content += "## Previous Agent Outputs:\n"
                    for agent_id, output in context["previous_outputs"].items():
                        user_content += f"\n### {agent_id}:\n{output}\n"
                    user_content += "\n---\n\n"

                if context.get("query"):
                    user_content += f"## Original Query:\n{context['query']}\n\n"

            user_content += f"## Your Task:\n{prompt}"

            # Make the API call
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt or "You are a helpful AI assistant.",
                messages=[
                    {"role": "user", "content": user_content}
                ]
            )

            # Extract text from response
            if message.content and len(message.content) > 0:
                return message.content[0].text

            return ""

        except anthropic.APIError as e:
            raise LLMProviderError("anthropic", str(e))
        except Exception as e:
            raise LLMProviderError("anthropic", f"Unexpected error: {str(e)}")
