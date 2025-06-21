from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import List, Optional
import asyncio
import nest_asyncio
import os
import json
from .llm_adapter import LLMAdapter, ChatMessage
from .openai_adapter import OpenRouterAdapter

nest_asyncio.apply()

load_dotenv()

class MCP_ChatBot:

    def __init__(self, llm_adapter: Optional[LLMAdapter] = None, model: str = "openai/gpt-4o-mini"):
        # Initialize session and client objects
        self.session: ClientSession = None
        
        # Use provided adapter or default to OpenRouter
        if llm_adapter:
            self.llm_adapter = llm_adapter
        else:
            self.llm_adapter = OpenRouterAdapter(model=model)
            
        self.available_tools: List[dict] = []

    async def process_query(self, query):
        messages = [ChatMessage(role='user', content=query)]
        response = await self.llm_adapter.chat_completion(
            messages=messages,
            tools=self.available_tools,
            max_tokens=2024
        )
        
        process_query = True
        while process_query:
            
            if response.content:
                print(response.content)
                if not response.tool_calls:
                    process_query = False
            
            if response.tool_calls:
                messages.append(ChatMessage(
                    role='assistant',
                    content=response.content,
                    tool_calls=response.tool_calls
                ))
                
                for tool_call in response.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    tool_id = tool_call.id
                    
                    print(f"Calling tool {tool_name} with args {tool_args}")
                    
                    # Call tool through MCP session
                    result = await self.session.call_tool(tool_name, arguments=tool_args)
                    
                    messages.append(ChatMessage(
                        role="tool", 
                        tool_call_id=tool_id,
                        content=str(result.content)
                    ))
                
                response = await self.llm_adapter.chat_completion(
                    messages=messages,
                    tools=self.available_tools,
                    max_tokens=2024
                )
                
                if response.content and not response.tool_calls:
                    print(response.content)
                    process_query = False

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print(f"\nMCP Chatbot Started!")
        print(f"Provider: {self.llm_adapter.provider_name}")
        print(f"Model: {self.llm_adapter.model}")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
        
                if query.lower() == 'quit':
                    break
                    
                await self.process_query(query)
                print("\n")
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def connect_to_server_and_run(self):
        # Create server parameters for stdio connection
        server_params = StdioServerParameters(
            command="uv",  # Executable
            args=["run", "python", "servers/arxiv_server.py"],  # Updated to use our arxiv server
            env=None,  # Optional environment variables
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                # Initialize the connection
                await session.initialize()
    
                # List available tools
                response = await session.list_tools()
                
                tools = response.tools
                print("\nConnected to server with tools:", [tool.name for tool in tools])
                
                self.available_tools = [{
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                } for tool in response.tools]
    
                await self.chat_loop()


async def main():
    # You can customize the LLM here
    from .llm_factory import LLMFactory, LLM_CONFIGS
    
    # Option 1: Use predefined config
    config = LLM_CONFIGS.get("gpt4o-mini", LLM_CONFIGS["gpt4o-mini"])
    llm_adapter = LLMFactory.create_adapter(**config)
    
    # Option 2: Create custom adapter
    # llm_adapter = LLMFactory.create_adapter("openrouter", "anthropic/claude-3-sonnet")
    
    chatbot = MCP_ChatBot(llm_adapter=llm_adapter)
    await chatbot.connect_to_server_and_run()
  

if __name__ == "__main__":
    asyncio.run(main())