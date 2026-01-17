"""
Google Gemini LLM Provider
"""
from typing import Optional, Dict, Any
import google.generativeai as genai

from .base import BaseLLMProvider
from ..core.exceptions import LLMProviderError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider implementation"""

    def __init__(self, model: str = "gemini-1.5-flash", api_key: str = None, **kwargs):
        super().__init__(model, api_key, **kwargs)
        if not self.api_key:
            raise LLMProviderError("gemini", "API key is required")

        # Configure the API
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(model)

    @property
    def provider_name(self) -> str:
        return "google"

    async def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate response using Gemini"""
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
            response = self.client.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
            )

            # Extract text from response
            if response.text:
                return response.text

            return ""

        except Exception as e:
            raise LLMProviderError("gemini", f"Error: {str(e)}")
