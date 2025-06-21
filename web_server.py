from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
import json
import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path

# Add application directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "application"))

from multi_server_chatbot import MCP_ChatBot

# Global chatbot instance
chatbot_instance = None
chatbot_initialized = False

async def startup_event():
    """Initialize the chatbot when the server starts"""
    global chatbot_instance, chatbot_initialized
    
    print("🚀 Starting MCP Chatbot Web Server...")
    
    try:
        # Load server configuration
        with open("server_config.json", "r") as f:
            config = json.load(f)
        
        chatbot_instance = MCP_ChatBot()
        
        # Connect to all servers - handle nested structure
        if "mcpServers" in config:
            servers_config = config["mcpServers"]
        else:
            servers_config = config
            
        for server_name, server_config in servers_config.items():
            print(f"Connecting to {server_name}...")
            await chatbot_instance.connect_to_server(server_name, server_config)
        
        print("✅ All servers connected successfully!")
        chatbot_initialized = True
        
    except Exception as e:
        print(f"❌ Error initializing chatbot: {e}")
        chatbot_initialized = False

# Use lifespan events instead of deprecated on_event
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await startup_event()
    yield
    # Shutdown (cleanup if needed)
    pass

app = FastAPI(title="MCP Chatbot Web Interface", lifespan=lifespan)

# Serve static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="web"), name="static")

@app.get("/")
async def get_chat_page():
    """Serve the main chat page"""
    with open("web/index.html", "r") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    if not chatbot_initialized:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Chatbot not initialized. Please try again later."
        }))
        await websocket.close()
        return
    
    # Send initialization message
    await websocket.send_text(json.dumps({
        "type": "status",
        "message": f"🤖 Connected to {chatbot_instance.llm_adapter.provider_name} using {chatbot_instance.llm_adapter.model}",
        "provider": chatbot_instance.llm_adapter.provider_name,
        "model": chatbot_instance.llm_adapter.model,
        "caching": chatbot_instance.llm_adapter.enable_caching,
        "tools": len(chatbot_instance.available_tools)
    }))
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "chat":
                query = message_data.get("message", "").strip()
                
                if not query:
                    continue
                
                # Send user message back to client for display
                await websocket.send_text(json.dumps({
                    "type": "user_message",
                    "message": query
                }))
                
                # Process the query
                try:
                    # Capture the chatbot response with streaming
                    original_print = print
                    current_message = ""
                    token_info = ""
                    
                    def capture_print(*args, **kwargs):
                        nonlocal current_message, token_info
                        line = " ".join(str(arg) for arg in args)
                        
                        # Check if this is token information
                        if "🔢 Tokens:" in line:
                            token_info = line
                        else:
                            # Add to current message
                            if current_message:
                                current_message += "\n" + line
                            else:
                                current_message = line
                        
                        original_print(*args, **kwargs)
                    
                    # Temporarily replace print to capture output
                    import builtins
                    builtins.print = capture_print
                    
                    try:
                        await chatbot_instance.process_query(query)
                    finally:
                        # Restore original print
                        builtins.print = original_print
                    
                    # Send the response with token info if available
                    if current_message:
                        response_data = {
                            "type": "assistant_message",
                            "message": current_message
                        }
                        
                        # Add token info if available
                        if token_info:
                            response_data["tokens"] = token_info
                        
                        await websocket.send_text(json.dumps(response_data))
                    
                except Exception as e:
                    await websocket.send_text(json.dumps({
                        "type": "error", 
                        "message": f"Error processing query: {str(e)}"
                    }))
            
            elif message_data.get("type") == "clear":
                # Clear conversation history
                chatbot_instance.conversation_history = []
                await websocket.send_text(json.dumps({
                    "type": "status",
                    "message": "🧹 Conversation history cleared"
                }))
    
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    print("🌐 Starting MCP Chatbot Web Server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)