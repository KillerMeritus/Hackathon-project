"""
Google Gemini LLM Provider - Using REST API directly
"""
from typing import Optional, Dict, Any
import httpx

from .base import BaseLLMProvider
from ..core.exceptions import LLMProviderError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider implementation using REST API"""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, model: str = "gemini-2.0-flash", api_key: str = None, **kwargs):
        super().__init__(model, api_key, **kwargs)
        if not self.api_key:
            raise LLMProviderError("gemini", "API key is required")
        
        # Handle different model name formats
        # Strip "google/" prefix if present (OpenRouter format)
        if model.startswith("google/"):
            model = model.replace("google/", "")
        
        # Map common aliases
        model_aliases = {
            "gemini-flash-latest": "gemini-2.0-flash",
            "gemini-flash": "gemini-2.0-flash",
            "gemini-pro": "gemini-1.5-pro",
        }
        self.model_id = model_aliases.get(model, model)

    @property
    def provider_name(self) -> str:
        return "google"

    async def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate response using Gemini REST API"""
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

            # Build request payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": full_prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "maxOutputTokens": self.max_tokens,
                    "temperature": self.temperature,
                }
            }

            # Make API request
            url = f"{self.BASE_URL}/models/{self.model_id}:generateContent?key={self.api_key}"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                    raise LLMProviderError("gemini", f"API Error ({response.status_code}): {error_msg}")
                
                result = response.json()
                
                # Extract text from response
                candidates = result.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                
                return ""

        except httpx.RequestError as e:
            raise LLMProviderError("gemini", f"Request failed: {str(e)}")
        except Exception as e:
            if isinstance(e, LLMProviderError):
                raise
            raise LLMProviderError("gemini", f"Error: {str(e)}")
