# Neural Chat Engine

A comprehensive ChatGPT-like chat engine built with Django and React, featuring MCP (Model Context Protocol) server support for extensible AI tool integration.

## 🚀 Features

### Core Architecture
- **Backend**: Django REST Framework with MongoDB for chat storage
- **Frontend**: React-based chat interface (to be implemented)
- **Authentication**: SQLite-based user management with token authentication
- **Real-time**: WebSocket support via Django Channels and Redis
- **MCP Integration**: Support for stdio, HTTP, SSE, and streamable_http transports

### MCP Server Support
- **Multi-Transport**: stdio, HTTP, Server-Sent Events (SSE), and Streamable HTTP
- **Tool Management**: Unified interface for MCP tools with enable/disable functionality
- **Auto-Discovery**: Automatic tool loading from configured MCP servers
- **Async Processing**: Full async support for MCP server communication

### Chat System
- **MongoDB Integration**: High-performance chat and message storage
- **User Management**: Django-based authentication with SQLite
- **Real-time Messaging**: WebSocket support for live chat updates
- **Message History**: Efficient pagination and retrieval
- **Chat Statistics**: Detailed analytics for users and conversations

## 📋 Architecture Overview

```
Neural Chat Engine
├── Django Backend (Port 8000)
│   ├── REST API Endpoints
│   ├── MongoDB Chat Storage
│   ├── SQLite User Management
│   └── MCP Server Integration
├── React Frontend (Port 3000)
│   ├── Chat Interface
│   ├── Tool Management
│   └── Real-time Updates
├── Redis (Port 6379)
│   ├── WebSocket Channel Layer
│   └── Task Queue
└── MCP Servers
    ├── STDIO Servers (Local)
    ├── HTTP Servers (Remote)
    ├── SSE Servers (Remote)
    └── Streamable HTTP (Remote)
```

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- Node.js 16+
- MongoDB (running on localhost:27017)
- Redis (running on localhost:6379)

### Backend Setup

1. **Clone and navigate to the project**:
   ```bash
   cd NeuralProtocol-
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations**:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Start the server**:
   ```bash
   python manage.py runserver
   ```

### MCP Servers Setup

1. **Start the example math server**:
   ```bash
   python mcp_servers/stdio_math_server.py
   ```

2. **Configure MCP servers** in `mcp_servers_config.json`:
   ```json
   {
     "mcpServers": {
       "stdio_math_server": {
         "transport": "stdio",
         "command": "python",
         "args": ["mcp_servers/stdio_math_server.py"]
       }
     }
   }
   ```

## 📡 API Endpoints

### Authentication
- `POST /api/v1/auth/token/` - Get authentication token

### Chat Management
- `GET /api/v1/chats/` - List user chats
- `POST /api/v1/chats/` - Create new chat
- `GET /api/v1/chats/{id}/` - Get specific chat
- `PUT/PATCH /api/v1/chats/{id}/` - Update chat
- `DELETE /api/v1/chats/{id}/` - Delete chat

### Messages
- `GET /api/v1/chats/{id}/messages/` - Get chat messages
- `POST /api/v1/chats/{id}/add_message/` - Add message to chat
- `POST /api/v1/chats/{id}/process/` - Process user message with AI

### Statistics
- `GET /api/v1/stats/` - Get user statistics
- `GET /api/v1/chats/{id}/stats/` - Get chat statistics

### MCP Tools
- `GET /api/v1/tools/` - List available MCP tools
- `POST /api/v1/tools/execute/` - Execute MCP tool
- `POST /api/v1/tools/{name}/enable/` - Enable tool
- `POST /api/v1/tools/{name}/disable/` - Disable tool

## 🔧 Configuration

### Environment Variables (.env)
```env
# MongoDB Configuration
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=neural_chat

# Redis Configuration  
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# LLM API Keys
GOOGLE_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Django Settings
SECRET_KEY=your_secret_key
DEBUG=True
```

### MCP Server Configuration
Edit `mcp_servers_config.json` to configure MCP servers:

```json
{
  "mcpServers": {
    "stdio_math_server": {
      "transport": "stdio",
      "command": "python",
      "args": ["mcp_servers/stdio_math_server.py"]
    },
    "http_server": {
      "transport": "http",
      "url": "http://localhost:8005"
    },
    "sse_server": {
      "transport": "sse", 
      "url": "http://localhost:8006/sse"
    },
    "streamable_server": {
      "transport": "streamable_http",
      "url": "http://localhost:8007/mcp"
    }
  }
}
```

## 🧩 MCP Server Integration

The system supports four MCP transport types:

### 1. STDIO Transport
- **Use Case**: Local Python/Node.js servers
- **Communication**: Standard input/output
- **Example**: Math server, file operations, local tools

### 2. HTTP Transport  
- **Use Case**: REST API-based services
- **Communication**: HTTP requests
- **Example**: Web services, databases, external APIs

### 3. Server-Sent Events (SSE)
- **Use Case**: Real-time streaming data
- **Communication**: EventSource/SSE
- **Example**: Live data feeds, monitoring, notifications

### 4. Streamable HTTP
- **Use Case**: Bidirectional streaming
- **Communication**: HTTP with streaming
- **Example**: Large data processing, real-time analysis

## 📊 Data Models

### Chat Schema (MongoDB)
```javascript
{
  _id: ObjectId,
  user_id: Number,      // Django User ID
  title: String,
  created_at: Date,
  updated_at: Date,
  message_count: Number,
  metadata: Object,
  is_active: Boolean
}
```

### Message Schema (MongoDB)
```javascript
{
  _id: ObjectId,
  chat_id: ObjectId,
  role: String,         // 'user', 'assistant', 'system'
  content: String,
  created_at: Date,
  metadata: Object,
  tokens: Number
}
```

## 🔐 Security Features

- **Authentication**: Token-based authentication
- **CORS**: Configured for React frontend
- **Input Validation**: Pydantic serializers
- **SQL Injection**: MongoDB aggregation pipeline protection
- **Rate Limiting**: Built-in Django REST framework throttling
- **Tool Approval**: Optional approval workflow for MCP tools

## 🚧 TODO / Next Steps

1. **Frontend Implementation**:
   - React chat interface
   - Real-time message updates
   - Tool management UI
   - User authentication flow

2. **Enhanced Features**:
   - File upload support
   - Voice message integration
   - Chat export functionality
   - Advanced search capabilities

3. **Production Setup**:
   - Docker containerization
   - Nginx reverse proxy
   - SSL/TLS configuration
   - Monitoring and logging

4. **LLM Integration**:
   - Complete Langchain integration
   - Streaming response support
   - Tool execution in chat context
   - Multi-model support

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Django REST Framework
- MCP (Model Context Protocol) integration
- Inspired by ChatGPT architecture
- MongoDB for high-performance chat storage