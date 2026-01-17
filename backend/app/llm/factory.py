"""
LLM Provider Factory - creates provider instances based on configuration
"""
from typing import Dict, Any, Optional

from .base import BaseLLMProvider
from .claude import ClaudeProvider
from .openai_llm import OpenAIProvider
from .gemini import GeminiProvider
from ..config import get_api_key
from ..core.exceptions import LLMProviderError


# Registry of available providers
PROVIDER_REGISTRY = {
    "anthropic": ClaudeProvider,
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
    "gpt": OpenAIProvider,
    "google": GeminiProvider,
    "gemini": GeminiProvider,
}

# Default models for each provider
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-20250514",
    "claude": "claude-sonnet-4-20250514",
    "openai": "gpt-4o",
    "gpt": "gpt-4o",
    "google": "gemini-1.5-flash",
    "gemini": "gemini-1.5-flash",
}


def get_llm_provider(
    provider_name: str,
    model_config: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None
) -> BaseLLMProvider:
    """
    Factory function to create LLM provider instances

    Args:
        provider_name: Name of the provider (claude, openai, gemini, etc.)
        model_config: Optional model configuration dict
        api_key: Optional API key override

    Returns:
        Configured LLM provider instance
    """
    provider_name_lower = provider_name.lower()

    # Get provider class
    provider_class = PROVIDER_REGISTRY.get(provider_name_lower)
    if not provider_class:
        available = ", ".join(set(PROVIDER_REGISTRY.keys()))
        raise LLMProviderError(
            provider_name,
            f"Unknown provider. Available: {available}"
        )

    # Get API key
    if not api_key:
        # Map provider names to API key names
        key_mapping = {
            "claude": "anthropic",
            "gpt": "openai",
        }
        key_name = key_mapping.get(provider_name_lower, provider_name_lower)
        api_key = get_api_key(key_name)

    if not api_key:
        raise LLMProviderError(
            provider_name,
            f"API key not found. Set the appropriate environment variable."
        )

    # Build kwargs from model_config
    kwargs = {}
    if model_config:
        kwargs['max_tokens'] = model_config.get('max_tokens', 4096)
        kwargs['temperature'] = model_config.get('temperature', 0.7)
        model = model_config.get('model', DEFAULT_MODELS.get(provider_name_lower))
    else:
        model = DEFAULT_MODELS.get(provider_name_lower)

    # Create and return provider instance
    return provider_class(model=model, api_key=api_key, **kwargs)


def get_provider_for_agent(
    agent_model: str,
    models_config: Dict[str, Any]
) -> BaseLLMProvider:
    """
    Get LLM provider for an agent based on its model setting

    Args:
        agent_model: Model name from agent config (e.g., "claude", "openai", or custom)
        models_config: Models configuration from YAML

    Returns:
        Configured LLM provider
    """
    # Check if it's a custom model definition
    if agent_model in models_config:
        model_cfg = models_config[agent_model]
        provider_name = model_cfg.provider if hasattr(model_cfg, 'provider') else model_cfg.get('provider')
        return get_llm_provider(
            provider_name,
            model_config={
                'model': model_cfg.model if hasattr(model_cfg, 'model') else model_cfg.get('model'),
                'max_tokens': model_cfg.max_tokens if hasattr(model_cfg, 'max_tokens') else model_cfg.get('max_tokens', 4096),
                'temperature': model_cfg.temperature if hasattr(model_cfg, 'temperature') else model_cfg.get('temperature', 0.7),
            }
        )

    # It's a direct provider name (claude, openai, gemini)
    return get_llm_provider(agent_model)
