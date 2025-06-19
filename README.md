# MCP Study Project

A comprehensive study and implementation of Model Context Protocol (MCP) servers and chatbot applications.

## 🚀 Project Overview

This project demonstrates the power of MCP by building:
- **ArXiv Research Server** - Search and analyze academic papers
- **Multi-Server Chatbot** - Intelligent assistant with multiple capabilities
- **OpenRouter Integration** - Cost-effective LLM integration

## 📁 Project Structure

```
mcp_study/
├── servers/
│   └── arxiv_server.py          # ArXiv paper search MCP server
├── application/
│   ├── chatbot.py               # Single-server chatbot
│   └── multi_server_chatbot.py  # Multi-server chatbot
├── server_config.json           # MCP server configuration
├── troubleshooting-2025-06-19.md # Debugging documentation
└── .env.example                 # Environment configuration
```

## 🛠️ Setup

1. **Clone and install dependencies**:
   ```bash
   git clone <your-repo>
   cd mcp_study
   uv sync
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Add your OPENROUTER_API_KEY
   ```

3. **Install MCP dependencies**:
   ```bash
   npm install -g @modelcontextprotocol/inspector
   npm install -g @modelcontextprotocol/server-filesystem
   uvx install mcp-server-fetch
   ```

## 🔧 Usage

### Testing Servers with Inspector

Test individual MCP servers:
```bash
npx @modelcontextprotocol/inspector uv run python servers/arxiv_server.py
```

### Single-Server Chatbot

Basic chatbot with ArXiv research capabilities:
```bash
uv run application/chatbot.py
```

### Multi-Server Chatbot

Advanced chatbot with multiple capabilities:
```bash
uv run application/multi_server_chatbot.py
```

## 🤖 Available Capabilities

### 🔬 Research (ArXiv Server)
- Search academic papers by topic
- Extract detailed paper information
- Generate research summaries

### 📁 Filesystem
- Read and write files
- Directory management
- File operations

### 🌐 Web Fetch
- Retrieve web content
- Process online resources
- Integrate web data with research

## 📝 Example Queries

Try these with the multi-server chatbot:

```
"Search for 5 papers about machine learning and save summaries to a file"

"Fetch content from https://example.com and compare it with recent research papers"

"Create a research report on neural networks combining web sources and academic papers"
```

## 🐛 Troubleshooting

See `troubleshooting-2025-06-19.md` for detailed debugging information, including:
- Filename conflict resolution
- Import issues with Python modules
- MCP Inspector timeout solutions

## 🎯 Key Learnings

1. **Choose the right model** - GPT-4o-mini vs weaker models for function calling
2. **Avoid over-engineering** - Simple code with capable models beats complex error handling
3. **MCP power** - Easy integration of multiple specialized tools
4. **Cost-effective AI** - OpenRouter provides affordable access to powerful models

## 📦 Dependencies

- **Python 3.13+** with uv package manager
- **OpenRouter API** for LLM access
- **MCP Servers** for specialized capabilities
- **Node.js** for MCP inspector and filesystem server

## 🚀 Next Steps

- Add more specialized MCP servers
- Implement conversation memory
- Create web interface
- Add streaming responses
