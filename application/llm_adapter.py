from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Any]] = None
    tool_call_id: Optional[str] = None


@dataclass
class ChatResponse:
    content: Optional[str]
    tool_calls: Optional[List[Any]] = None
    usage: Optional[Dict[str, int]] = None


class LLMAdapter(ABC):
    """Abstract base class for LLM adapters"""
    
    def __init__(self, model: str, **kwargs):
        self.model = model
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