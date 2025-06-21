from typing import Dict, Type
from llm_adapter import LLMAdapter
from openai_adapter import OpenAIAdapter, OpenRouterAdapter


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
        "enable_caching": True,
        "cache_system_messages": True,
    },
    "gpt4o-mini": {
        "provider": "openrouter", 
        "model": "openai/gpt-4o-mini",
        "enable_caching": True,
        "cache_system_messages": True,
    },
    "gpt4.1-mini": {
        "provider": "openrouter",
        "model": "openai/gpt-4.1-mini", 
        "enable_caching": True,
        "cache_system_messages": True,
    },
    "claude-sonnet": {
        "provider": "openrouter",
        "model": "anthropic/claude-3-sonnet",
        "enable_caching": True,
        "cache_system_messages": True,
    },
    "claude-haiku": {
        "provider": "openrouter",
        "model": "anthropic/claude-3-haiku", 
        "enable_caching": True,
        "cache_system_messages": True,
    },
    "llama-70b": {
        "provider": "openrouter",
        "model": "meta-llama/llama-3-70b-instruct",
        "enable_caching": False,  # DeepSeek has automatic caching, Llama may not support it
        "cache_system_messages": False,
    },
    # Caching-optimized configs
    "claude-sonnet-cached": {
        "provider": "openrouter",
        "model": "anthropic/claude-3-sonnet",
        "enable_caching": True,
        "cache_system_messages": True,
    }
}