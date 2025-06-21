import openai
import os
from typing import List, Dict, Any, Optional
from llm_adapter import LLMAdapter, ChatMessage, ChatResponse, CacheControl


class OpenAIAdapter(LLMAdapter):
    """OpenAI API adapter (works with OpenAI and OpenRouter)"""
    
    def __init__(self, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs):
        # Extract our custom parameters before passing to parent
        enable_caching = kwargs.pop('enable_caching', True)
        cache_system_messages = kwargs.pop('cache_system_messages', True)
        
        super().__init__(model, enable_caching=enable_caching, cache_system_messages=cache_system_messages)
        
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url,
            **kwargs  # Now only contains OpenAI-compatible parameters
        )
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> ChatResponse:
        # Apply caching to messages if enabled
        processed_messages = []
        for msg in messages:
            cached_msg = self.add_cache_breakpoint(msg)
            processed_messages.append(cached_msg)
        
        # Convert our ChatMessage format to OpenAI format
        openai_messages = []
        for msg in processed_messages:
            openai_msg = {"role": msg.role}
            
            # Handle content with cache_control for Anthropic/Gemini
            if msg.content and msg.cache_control and self.requires_manual_cache_control:
                openai_msg["content"] = [
                    {
                        "type": "text",
                        "text": msg.content,
                        "cache_control": {"type": msg.cache_control.type}
                    }
                ]
            elif msg.content:
                openai_msg["content"] = msg.content
                
            if msg.tool_calls:
                openai_msg["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                openai_msg["tool_call_id"] = msg.tool_call_id
            openai_messages.append(openai_msg)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            tools=tools,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        
        choice = response.choices[0]
        return ChatResponse(
            content=choice.message.content,
            tool_calls=choice.message.tool_calls,
            usage=response.usage.model_dump() if response.usage else None
        )
    
    def get_available_models(self) -> List[str]:
        # This would ideally fetch from the API, but for now return common models
        return [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ]
    
    @property
    def provider_name(self) -> str:
        return "OpenAI"
    
    @property
    def supports_caching(self) -> bool:
        return True  # OpenAI supports automatic caching
    
    @property
    def requires_manual_cache_control(self) -> bool:
        return False  # OpenAI has automatic caching


class OpenRouterAdapter(OpenAIAdapter):
    """OpenRouter adapter - extends OpenAI adapter with OpenRouter specifics"""
    
    def __init__(self, model: str, **kwargs):
        # Extract our custom parameters
        enable_caching = kwargs.get('enable_caching', True)
        cache_system_messages = kwargs.get('cache_system_messages', True)
        
        super().__init__(
            model=model,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            enable_caching=enable_caching,
            cache_system_messages=cache_system_messages
        )
    
    def get_available_models(self) -> List[str]:
        return [
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "openai/gpt-4.1-mini",
            "openai/gpt-4.1",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku",
            "meta-llama/llama-3-70b-instruct",
            "google/gemini-pro"
        ]
    
    @property
    def provider_name(self) -> str:
        return "OpenRouter"
    
    @property
    def supports_caching(self) -> bool:
        return True  # OpenRouter supports caching for multiple providers
    
    @property
    def requires_manual_cache_control(self) -> bool:
        # Anthropic and Gemini models need manual cache_control
        return any(provider in self.model.lower() for provider in ["anthropic", "claude", "gemini"])
    
    def _is_openai_model(self) -> bool:
        """Check if the model is an OpenAI model (automatic caching)"""
        return "openai/" in self.model.lower() or "gpt" in self.model.lower()