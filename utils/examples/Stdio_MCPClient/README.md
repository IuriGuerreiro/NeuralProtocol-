# MCP Server Manager with Gemini Integration

This MCP (Model Context Protocol) server manager has been updated to use Google's Gemini AI instead of Groq.

## 🚀 Features

- **Gemini AI Integration**: Uses Google's Gemini 2.0 Flash model
- **MCP Server Management**: Connects to and manages multiple MCP servers
- **Tool Execution**: Executes tools from connected servers
- **Retry Mechanism**: Built-in retry logic for failed tool executions
- **Async Support**: Full async/await support for better performance

## 🔧 Setup

### 1. Install Dependencies

```bash
cd NeuralProtocol-/utils
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and add your Google API key:

```bash
cp env_example.txt .env
# Edit .env and add your GOOGLE_API_KEY
```

### 3. Server Configuration

Create a `servers_config.json` file in the same directory:

```json
{
    "mcpServers": {
        "terminal_server": {
            "transport": "stdio",
            "command": "python",
            "args": ["../../src/MCPServers/terminal_server.py"]
        },
        "http_math_server": {
            "transport": "http",
            "url": "http://localhost:8000"
        }
    }
}
```

## 🎯 Usage

### Basic Usage

```bash
python MCP_server_manager.py
```

### Interactive Commands

- Type your questions naturally
- The system will automatically detect when tools are needed
- Use `quit` or `exit` to close the session

### Tool Execution

The system automatically:
1. Analyzes your request
2. Determines if tools are needed
3. Executes the appropriate tool
4. Provides a natural response

## 🔌 Supported Server Types

### Stdio Servers
- Direct Python script execution
- Command-line tool integration
- Local development and testing

### HTTP Servers
- REST API integration
- Remote tool execution
- Scalable architecture

## 🛠️ Available Tools

Tools depend on your configured MCP servers:

- **Terminal Server**: File operations, system commands
- **Math Server**: Mathematical calculations
- **Custom Servers**: Any MCP-compliant server

## 🔍 Troubleshooting

### Common Issues

1. **API Key Error**: Ensure `GOOGLE_API_KEY` is set in `.env`
2. **Server Connection Failed**: Check if MCP servers are running
3. **Tool Not Found**: Verify server configuration and tool names

### Debug Mode

The system provides detailed logging:
- Server connection status
- Tool execution attempts
- Error details and retry information

## 📊 Performance

- **Response Time**: 1-3 seconds (depending on tool complexity)
- **Concurrent Support**: Multiple server connections
- **Memory Efficient**: Minimal memory footprint
- **Scalable**: Easy to add new servers and tools

## 🔮 Future Enhancements

1. **Streaming Responses**: Real-time tool execution updates
2. **Web Interface**: Modern web UI for server management
3. **Plugin System**: Easy addition of new server types
4. **Advanced Caching**: Tool result caching for better performance

## 📚 API Reference

### Configuration Class
- `load_env()`: Load environment variables
- `load_config(file_path)`: Load server configuration
- `llm_api_key`: Get configured API key

### Server Class
- `initialize()`: Connect to MCP server
- `list_tools()`: Get available tools
- `execute_tool(name, args)`: Execute specific tool
- `cleanup()`: Close server connection

### LLMClient Class
- `get_response(messages)`: Get Gemini AI response
- Automatic message format conversion
- Error handling and fallback responses

### ChatSession Class
- `start()`: Begin interactive session
- `process_llm_response(response)`: Handle tool execution
- `cleanup_servers()`: Proper resource cleanup

## 🤝 Contributing

To extend the system:

1. **Add New Server Types**: Extend the Server class
2. **Custom Tools**: Implement MCP-compliant servers
3. **Enhanced LLM Integration**: Modify LLMClient for different models
4. **UI Improvements**: Add web or desktop interfaces

---

**MCP Server Manager with Gemini** - Where AI meets protocol! 🚀
