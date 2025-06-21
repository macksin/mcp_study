from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class CacheControl:
    type: str = "ephemeral"

@dataclass
class ChatMessage:
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Any]] = None
    tool_call_id: Optional[str] = None
    cache_control: Optional[CacheControl] = None


@dataclass
class ChatResponse:
    content: Optional[str]
    tool_calls: Optional[List[Any]] = None
    usage: Optional[Dict[str, int]] = None


class LLMAdapter(ABC):
    """Abstract base class for LLM adapters"""
    
    def __init__(self, model: str, enable_caching: bool = True, cache_system_messages: bool = True, **kwargs):
        self.model = model
        self.enable_caching = enable_caching
        self.cache_system_messages = cache_system_messages
        self.config = kwargs
    
    @abstractmethod
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> ChatResponse:
        """Generate a chat completion"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the LLM provider"""
        pass
    
    @property
    @abstractmethod
    def supports_caching(self) -> bool:
        """Whether this provider supports prompt caching"""
        pass
    
    @property
    @abstractmethod
    def requires_manual_cache_control(self) -> bool:
        """Whether this provider requires manual cache_control breakpoints"""
        pass
    
    def add_cache_breakpoint(self, message: ChatMessage, cache_large_content: bool = True) -> ChatMessage:
        """Add cache breakpoint to message if appropriate"""
        if not self.enable_caching or not self.supports_caching:
            return message
            
        # Only add cache control for providers that require it
        if not self.requires_manual_cache_control:
            return message
            
        # Add cache control to system messages if enabled
        if message.role == "system" and self.cache_system_messages:
            message.cache_control = CacheControl()
        
        # Add cache control to large content (tool results, etc.)
        elif cache_large_content and message.content and len(message.content) > 1000:
            message.cache_control = CacheControl()
            
        return message