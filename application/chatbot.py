from dotenv import load_dotenv
import openai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import List
import asyncio
import nest_asyncio
import os
import json

nest_asyncio.apply()

load_dotenv()

class MCP_ChatBot:

    def __init__(self):
        # Initialize session and client objects
        self.session: ClientSession = None
        # Configure OpenAI client for OpenRouter
        self.client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        self.available_tools: List[dict] = []
        self.model = "openai/gpt-4o-mini"

    async def process_query(self, query):
        messages = [{'role':'user', 'content':query}]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.available_tools,  # tools exposed to the LLM
            max_tokens=2024
        )
        
        process_query = True
        while process_query:
            assistant_message = response.choices[0].message
            
            if assistant_message.content:
                print(assistant_message.content)
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
                    
                    # Call tool through MCP session
                    result = await self.session.call_tool(tool_name, arguments=tool_args)
                    
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
                
                if response.choices[0].message.content and not response.choices[0].message.tool_calls:
                    print(response.choices[0].message.content)
                    process_query = False

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print(f"\nMCP Chatbot Started! Using model: {self.model}")
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
    chatbot = MCP_ChatBot()
    await chatbot.connect_to_server_and_run()
  

if __name__ == "__main__":
    asyncio.run(main())