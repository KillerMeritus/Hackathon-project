"""
LLM Factory - Creates LLM providers based on configuration
"""
from typing import Dict, Any

from .base import BaseLLMProvider
from .openai_llm import OpenAIProvider
from .claude import ClaudeProvider
from .gemini import GeminiProvider
from ..config import get_api_key
from ..core.exceptions import LLMProviderError


# Maps provider names to classes
PROVIDERS = {
    "openai": OpenAIProvider,
    "claude": ClaudeProvider,
    "gemini": GeminiProvider,
}


# Default models if not specified in config
DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "claude": "claude-sonnet-4-20240514",
    "gemini": "gemini-1.5-flash",
}


def get_provider_for_agent(
    model_name: str,
    models_config: Dict[str, Any]
) -> BaseLLMProvider:
    """
    Factory function to create an LLM provider.

    model_name: provider name from YAML (openai / claude / gemini)
    models_config: config block from YAML
    """
    model_lower = model_name.lower()

    provider_class = PROVIDERS.get(model_lower)
    if not provider_class:
        raise LLMProviderError(model_name, f"Unknown provider: {model_name}")

    api_key = get_api_key(model_lower)

    config = models_config.get(model_name, {})
    actual_model = config.get("model", DEFAULT_MODELS.get(model_lower))
    max_tokens = config.get("max_tokens", 4096)
    temperature = config.get("temperature", 0.7)

    return provider_class(
        model=actual_model,
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature
    )
