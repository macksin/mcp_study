from typing import Dict, Type
from .llm_adapter import LLMAdapter
from .openai_adapter import OpenAIAdapter, OpenRouterAdapter


class LLMFactory:
    """Factory for creating LLM adapters"""
    
    _adapters: Dict[str, Type[LLMAdapter]] = {
        "openai": OpenAIAdapter,
        "openrouter": OpenRouterAdapter,
    }
    
    @classmethod
    def create_adapter(cls, provider: str, model: str, **kwargs) -> LLMAdapter:
        """Create an adapter instance"""
        if provider not in cls._adapters:
            raise ValueError(f"Unknown provider: {provider}. Available: {list(cls._adapters.keys())}")
        
        adapter_class = cls._adapters[provider]
        return adapter_class(model=model, **kwargs)
    
    @classmethod
    def register_adapter(cls, name: str, adapter_class: Type[LLMAdapter]):
        """Register a new adapter type"""
        cls._adapters[name] = adapter_class
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available providers"""
        return list(cls._adapters.keys())


# Predefined configurations for common setups
LLM_CONFIGS = {
    "gpt4o": {
        "provider": "openrouter",
        "model": "openai/gpt-4o",
    },
    "gpt4o-mini": {
        "provider": "openrouter", 
        "model": "openai/gpt-4o-mini",
    },
    "claude-sonnet": {
        "provider": "openrouter",
        "model": "anthropic/claude-3-sonnet",
    },
    "claude-haiku": {
        "provider": "openrouter",
        "model": "anthropic/claude-3-haiku", 
    },
    "llama-70b": {
        "provider": "openrouter",
        "model": "meta-llama/llama-3-70b-instruct",
    }
}