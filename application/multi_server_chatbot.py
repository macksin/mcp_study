from dotenv import load_dotenv
import openai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import List, Dict, TypedDict
from contextlib import AsyncExitStack
import json
import asyncio
import os

load_dotenv()

class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict

class MCP_ChatBot:

    def __init__(self):
        # Initialize session and client objects
        self.sessions: List[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        # Configure OpenAI client for OpenRouter
        self.client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        self.model = "openai/gpt-4o-mini"
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}
        # Multi-turn conversation state
        self.conversation_history: List[dict] = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single MCP server."""
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self.sessions.append(session)
            
            # List available tools for this session
            response = await session.list_tools()
            tools = response.tools
            print(f"\nConnected to {server_name} with tools:", [t.name for t in tools])
            
            for tool in tools:
                self.tool_to_session[tool.name] = session
                self.available_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")

    async def connect_to_servers(self):
        """Connect to all configured MCP servers."""
        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)
            
            servers = data.get("mcpServers", {})
            
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
                
            print(f"\nTotal tools available: {len(self.available_tools)}")
            print("Tool names:", [tool["function"]["name"] for tool in self.available_tools])
            
        except Exception as e:
            print(f"Error loading server configuration: {e}")
            raise
    
    def format_tokens(self, count: int) -> str:
        """Format token count with nice indicators"""
        if count >= 1000:
            return f"{count/1000:.1f}k"
        return str(count)
    
    def print_token_usage(self, input_tokens: int, output_tokens: int):
        """Print token usage with nice formatting"""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        
        input_str = self.format_tokens(input_tokens)
        output_str = self.format_tokens(output_tokens)
        total_input_str = self.format_tokens(self.total_input_tokens)
        total_output_str = self.format_tokens(self.total_output_tokens)
        
        print(f"🔢 Tokens: {input_str}/{output_str} (Total: {total_input_str}/{total_output_str})")

    async def process_query(self, query):
        # Add user message to conversation history
        self.conversation_history.append({'role': 'user', 'content': query})
        
        # Use full conversation history for context
        messages = self.conversation_history.copy()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.available_tools,
            max_tokens=2024
        )
        
        # Track token usage
        if hasattr(response, 'usage') and response.usage:
            self.print_token_usage(response.usage.prompt_tokens, response.usage.completion_tokens)
        
        assistant_response_content = None
        process_query = True
        while process_query:
            assistant_message = response.choices[0].message
            
            if assistant_message.content:
                print(assistant_message.content)
                assistant_response_content = assistant_message.content
                if not assistant_message.tool_calls:
                    process_query = False
            
            if assistant_message.tool_calls:
                messages.append({
                    'role': 'assistant',
                    'content': assistant_message.content,
                    'tool_calls': assistant_message.tool_calls
                })
                
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    tool_id = tool_call.id
                    
                    print(f"Calling tool {tool_name} with args {tool_args}")
                    
                    # Get the session for this specific tool
                    session = self.tool_to_session[tool_name]
                    result = await session.call_tool(tool_name, arguments=tool_args)
                    
                    messages.append({
                        "role": "tool", 
                        "tool_call_id": tool_id,
                        "content": str(result.content)
                    })
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.available_tools,
                    max_tokens=2024
                )
                
                # Track token usage for follow-up calls
                if hasattr(response, 'usage') and response.usage:
                    self.print_token_usage(response.usage.prompt_tokens, response.usage.completion_tokens)
                
                if response.choices[0].message.content and not response.choices[0].message.tool_calls:
                    assistant_response_content = response.choices[0].message.content
                    print(response.choices[0].message.content)
                    process_query = False
        
        # Add assistant response to conversation history
        if assistant_response_content:
            self.conversation_history.append({'role': 'assistant', 'content': assistant_response_content})

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print(f"\n🤖 Multi-Server MCP Chatbot Started! Using model: {self.model}")
        print("✨ Features: Multi-turn conversation + Token tracking")
        print("\nAvailable capabilities:")
        print("  🔬 Research: ArXiv paper search and analysis")
        print("  📁 Filesystem: File operations and management")
        print("  🌐 Fetch: Web content retrieval")
        print("\n💡 Special commands:")
        print("  'clear' - Clear conversation history")
        print("  'history' - Show conversation history")
        print("  'quit' - Exit chatbot")
        print("\nType your queries to start chatting...")
        
        while True:
            try:
                query = input(f"\n[Turn {len(self.conversation_history)//2 + 1}] Query: ").strip()
        
                if query.lower() == 'quit':
                    break
                elif query.lower() == 'clear':
                    self.conversation_history = []
                    self.total_input_tokens = 0
                    self.total_output_tokens = 0
                    print("🧹 Conversation history and token counts cleared!")
                    continue
                elif query.lower() == 'history':
                    print(f"\n📜 Conversation History ({len(self.conversation_history)} messages):")
                    for i, msg in enumerate(self.conversation_history):
                        role_emoji = "🧑" if msg['role'] == 'user' else "🤖"
                        print(f"  {i+1}. {role_emoji} {msg['role']}: {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")
                    continue
                    
                await self.process_query(query)
                    
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
    
    async def cleanup(self):
        """Cleanly close all resources using AsyncExitStack."""
        await self.exit_stack.aclose()

async def main():
    chatbot = MCP_ChatBot()
    try:
        await chatbot.connect_to_servers()
        await chatbot.chat_loop()
    finally:
        await chatbot.cleanup()

if __name__ == "__main__":
    asyncio.run(main())