# Langchain MCP Integration

This directory contains a new implementation that integrates Langchain with MCP (Model Context Protocol) stdio servers, providing a more flexible and modern approach to tool-enabled AI conversations.

## Features

### 🚀 Key Improvements over Original Implementation

1. **Langchain Integration**: Uses `langchain.chat_models.init_chat_model` for easy model switching between providers (Google, OpenAI, etc.)
2. **Pydantic Validation**: All tool calls, messages, and configurations are validated using Pydantic models
3. **React Agent**: Uses LangGraph's `create_react_agent` for sophisticated tool reasoning and execution
4. **Automatic Tool Loading**: Uses `langchain_mcp_adapters` to automatically load and adapt MCP tools for Langchain
5. **Better Error Handling**: Comprehensive error handling with detailed logging
6. **Configuration Validation**: Server configurations are validated using Pydantic models

### 🔧 Tools & Technologies

- **Langchain**: Model management and tool orchestration
- **LangGraph**: React agent for tool reasoning
- **Pydantic**: Data validation and serialization
- **MCP**: Model Context Protocol for tool integration
- **Google Gemini**: Default LLM (easily switchable)

## Files

- `langchain_mcp_chat.py`: Main implementation with Langchain + MCP integration
- `simple_servers_config.json`: Configuration for SQLite MCP server
- `MCP_server_manager.py`: Original implementation (for reference)

## Setup

1. **Environment Variables**: Set up your API keys in `.env`:
   ```bash
   GOOGLE_API_KEY=your_google_api_key_here
   # OR
   OPENAI_API_KEY=your_openai_api_key_here
   ```

2. **Virtual Environment**: Make sure you're in the project's virtual environment:
   ```bash
   # From project root
   .\venv\Scripts\Activate.ps1
   ```

3. **Dependencies**: All required packages should already be installed in the venv:
   - `langchain`
   - `langchain_mcp_adapters`
   - `langgraph`
   - `pydantic`
   - `mcp`
   - `google-generativeai`

## Usage

### Basic Usage

```bash
cd NeuralProtocol-\utils\examples\Stdio_MCPClient
python langchain_mcp_chat.py
```

### Available Commands

- `help`: Show available tools and commands
- `quit` or `exit`: End the chat session

### Example Conversation

```
💬 You: use the tools you got and create a table with the fields a b and c
🤖 Assistant: OK. I have created a table called `my_table` with columns `a`, `b`, and `c`, all of which are of type INTEGER.
```

## Configuration

### Server Configuration

The `simple_servers_config.json` file defines which MCP servers to load:

```json
{
    "mcpServers": {
        "sqlite": {
            "transport": "stdio",
            "command": "uvx",
            "args": ["mcp-server-sqlite", "--db-path", "./test.db"]
        }
    }
}
```

### Model Configuration

To switch models, modify the `initialize_llm` call in the code:

```python
# Google Gemini (default)
await self.initialize_llm("gemini-2.0-flash", "google_genai")

# OpenAI GPT-4
await self.initialize_llm("gpt-4", "openai")

# OpenAI GPT-3.5
await self.initialize_llm("gpt-3.5-turbo", "openai")
```

## Architecture

### Pydantic Models

- `ToolCall`: Validates tool execution requests
- `Message`: Validates chat messages with timestamps
- `ChatHistory`: Manages conversation history
- `ServerConfig`: Validates server configurations

### Key Classes

- `Configuration`: Manages environment variables and settings
- `Server`: Handles MCP server connections and tool loading
- `LangchainMCPChat`: Main orchestrator class
- `LangchainMCPChat.initialize_llm()`: Sets up the LLM
- `LangchainMCPChat.load_all_tools()`: Loads tools from all servers
- `LangchainMCPChat.create_agent()`: Creates the React agent
- `LangchainMCPChat.process_message()`: Handles user messages

### Flow

1. **Initialization**: Load config, initialize LLM, connect to MCP servers
2. **Tool Loading**: Use `langchain_mcp_adapters` to load and adapt tools
3. **Agent Creation**: Create React agent with LLM and tools
4. **Chat Loop**: Process user messages, execute tools as needed
5. **Cleanup**: Properly close all server connections

## Error Handling

- **Server Validation**: Invalid server configs are skipped with warnings
- **Transport Filtering**: Only stdio servers are supported (HTTP servers are skipped)
- **Connection Failures**: Servers that fail to initialize are cleaned up properly
- **Tool Execution**: Failed tool executions are logged and handled gracefully

## Logging

The application provides detailed logging with emojis for easy identification:

- 🚀 Startup messages
- ✅ Success operations  
- ❌ Error messages
- ⚠️ Warning messages
- 🔧 Tool-related messages
- 🤖 LLM/Agent messages
- 💬 Chat messages
- 🧹 Cleanup operations

## Troubleshooting

### Common Issues

1. **"No module named 'mcp'"**: Make sure you're in the virtual environment
2. **"API key not found"**: Set `GOOGLE_API_KEY` or `OPENAI_API_KEY` in your environment
3. **"Unsupported model_provider"**: Use correct provider names like `google_genai` instead of `google`
4. **"Server failed to initialize"**: Check if the server command is available (e.g., `uvx` for SQLite server)

### Supported MCP Servers

Currently tested with:
- ✅ SQLite server (`mcp-server-sqlite`)
- ⚠️ HTTP servers (skipped - stdio only)
- ❌ Custom terminal servers (may need debugging)

## Next Steps

- [ ] Add memory management for conversation history
- [ ] Implement message summarization for context management
- [ ] Add support for HTTP MCP servers
- [ ] Add conversation persistence
- [ ] Implement conversation branching
- [ ] Add more comprehensive error recovery



