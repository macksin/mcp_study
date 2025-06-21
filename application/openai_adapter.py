import openai
import os
from typing import List, Dict, Any, Optional
from .llm_adapter import LLMAdapter, ChatMessage, ChatResponse


class OpenAIAdapter(LLMAdapter):
    """OpenAI API adapter (works with OpenAI and OpenRouter)"""
    
    def __init__(self, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs):
        super().__init__(model, **kwargs)
        
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url,
            **kwargs
        )
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> ChatResponse:
        # Convert our ChatMessage format to OpenAI format
        openai_messages = []
        for msg in messages:
            openai_msg = {"role": msg.role}
            if msg.content:
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


class OpenRouterAdapter(OpenAIAdapter):
    """OpenRouter adapter - extends OpenAI adapter with OpenRouter specifics"""
    
    def __init__(self, model: str, **kwargs):
        super().__init__(
            model=model,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            **kwargs
        )
    
    def get_available_models(self) -> List[str]:
        return [
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku",
            "meta-llama/llama-3-70b-instruct",
            "google/gemini-pro"
        ]
    
    @property
    def provider_name(self) -> str:
        return "OpenRouter"