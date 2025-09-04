# NeuralProtocol Chat System

A full-stack chat system that transforms the CLI-based NeuralProtocol chat into a modern web application with REST API endpoints.

## System Architecture

### Backend (FastAPI)
- **API Server**: FastAPI-based REST API (`backend/api/chat_api.py`)
- **Chat Engine**: LangChain integration with MCP servers (`backend/chat/langchain_chat.py`)
- **Tool Integration**: Custom tools and MCP server orchestration
- **Session Management**: Multi-session chat support with persistent state

### Frontend (React + TypeScript)
- **Components**: Modern React components with TypeScript
- **Services**: API abstraction layer with error handling
- **Routing**: React Router integration with authentication
- **UI/UX**: Responsive design with real-time messaging

## Features

### Backend API Endpoints

#### Session Management
- `POST /api/chat/sessions` - Create new chat session
- `GET /api/chat/sessions` - List all active sessions
- `GET /api/chat/sessions/{sessionId}` - Get session details
- `DELETE /api/chat/sessions/{sessionId}` - Delete session

#### Messaging
- `POST /api/chat/sessions/{sessionId}/messages` - Send message and get response
- `GET /api/chat/sessions/{sessionId}/history` - Get chat history with pagination
- `DELETE /api/chat/sessions/{sessionId}/history` - Clear chat history

#### System Information
- `GET /api/chat/sessions/{sessionId}/status` - Get system status
- `GET /api/chat/sessions/{sessionId}/tools` - Get available tools
- `PUT /api/chat/sessions/{sessionId}/approval-mode` - Toggle tool approval mode
- `GET /api/chat/health` - API health check

### Frontend Features

#### Chat Interface
- **Multi-Session Support**: Create and switch between multiple chat sessions
- **Real-Time Messaging**: Send messages and receive AI responses
- **Message History**: View and manage conversation history
- **Session Management**: Create, rename, and delete chat sessions

#### UI Components
- **ChatInterface**: Main chat application container
- **ChatSidebar**: Session list and management
- **ChatMessage**: Individual message display with role-based styling
- **MessageInput**: Rich text input with keyboard shortcuts

## Installation & Setup

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd NeuralProtocol-/backend
   ```

2. **Install dependencies**:
   ```bash
   pip install fastapi uvicorn langchain google-generativeai pydantic
   ```

3. **Configure MCP servers** (create one of these files):
   - `servers_config.json` - Full MCP server configuration
   - `simple_servers_config.json` - Minimal configuration

4. **Set up environment variables**:
   ```bash
   export GOOGLE_API_KEY="your-google-api-key"
   # Add other API keys as needed
   ```

5. **Run the API server**:
   ```bash
   python run_chat_api.py
   ```
   
   Or with custom options:
   ```bash
   python run_chat_api.py --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd NeuralProtocol-/frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure API endpoint** (if needed):
   Edit `src/config/api.ts` to update `API_BASE_URL`

4. **Start development server**:
   ```bash
   npm start
   ```

## API Documentation

### Request/Response Models

#### Create Session Request
```json
{
  "session_name": "My Chat Session", // optional
  "model_name": "gemini-2.0-flash",  // optional
  "provider": "google_genai"         // optional
}
```

#### Send Message Request
```json
{
  "content": "Hello, how can you help me?"
}
```

#### Chat Response
```json
{
  "user_message": {
    "id": "uuid",
    "role": "user",
    "content": "Hello, how can you help me?",
    "timestamp": "2024-01-01T12:00:00Z",
    "session_id": "session-uuid"
  },
  "assistant_message": {
    "id": "uuid",
    "role": "assistant", 
    "content": "I can help you with various tasks...",
    "timestamp": "2024-01-01T12:00:01Z",
    "session_id": "session-uuid"
  },
  "session_id": "session-uuid"
}
```

## Usage Examples

### Using the Web Interface

1. **Access the application**: Navigate to `http://localhost:3000` (frontend) 
2. **Authenticate**: Log in with your credentials
3. **Start chatting**: 
   - Click "Start New Chat" or navigate to `/chat`
   - Type your message and press Enter
   - View AI responses in real-time
   - Manage multiple sessions using the sidebar

### Using the API Directly

#### Create a new session
```bash
curl -X POST "http://localhost:8000/api/chat/sessions" \
     -H "Content-Type: application/json" \
     -d '{"session_name": "Test Session"}'
```

#### Send a message
```bash
curl -X POST "http://localhost:8000/api/chat/sessions/{session_id}/messages" \
     -H "Content-Type: application/json" \
     -d '{"content": "What tools do you have access to?"}'
```

#### Get chat history
```bash
curl "http://localhost:8000/api/chat/sessions/{session_id}/history?limit=10"
```

## File Structure

```
NeuralProtocol-/
├── backend/
│   ├── api/
│   │   └── chat_api.py              # FastAPI endpoints
│   ├── chat/
│   │   └── langchain_chat.py        # Original CLI chat implementation
│   ├── utils/                       # MCP server utilities
│   └── run_chat_api.py             # API server runner
├── frontend/
│   └── src/
│       ├── components/
│       │   └── Chat/
│       │       ├── ChatInterface.tsx    # Main chat component
│       │       ├── ChatMessage.tsx      # Message display
│       │       ├── MessageInput.tsx     # Message input
│       │       ├── ChatSidebar.tsx      # Session sidebar
│       │       ├── *.css               # Component styles
│       │       └── index.ts            # Exports
│       ├── services/
│       │   └── chatService.ts          # API service layer
│       ├── config/
│       │   └── api.ts                  # API configuration
│       └── App.tsx                     # Updated routing
└── README_CHAT_SYSTEM.md              # This documentation
```

## Development Notes

### Key Design Decisions

1. **Session Isolation**: Each chat session runs independently with its own LLM instance
2. **Message Flow**: User message → API → LangChain → AI response → Frontend
3. **State Management**: Backend maintains session state, frontend handles UI state
4. **Error Handling**: Comprehensive error handling at API and UI levels
5. **Authentication**: Integrates with existing auth system

### Known Limitations

1. **In-Memory Storage**: Sessions are stored in memory (use database for production)
2. **Single Server**: No clustering support (sessions tied to specific server instance)
3. **No Real-Time**: Polling-based updates (consider WebSocket for real-time)
4. **Resource Management**: No automatic session cleanup

### Future Enhancements

1. **Database Integration**: PostgreSQL/MongoDB for persistent storage
2. **WebSocket Support**: Real-time message updates
3. **Session Sharing**: Multi-user session collaboration
4. **Advanced UI**: Message editing, reactions, file uploads
5. **Analytics**: Usage tracking and conversation analytics

## Troubleshooting

### Backend Issues

**Server won't start:**
- Check MCP server configuration files exist
- Verify API keys are set correctly
- Ensure all dependencies are installed

**API calls failing:**
- Check CORS configuration in `chat_api.py`
- Verify frontend API_BASE_URL matches backend port
- Check server logs for detailed errors

### Frontend Issues

**Components not rendering:**
- Verify all imports in `App.tsx` are correct
- Check console for TypeScript/JavaScript errors
- Ensure API endpoints return expected data structure

**Styling issues:**
- Verify all CSS files are imported correctly
- Check responsive design breakpoints
- Test in different browsers

### Integration Issues

**Authentication not working:**
- Verify JWT tokens are passed correctly
- Check API endpoint authentication requirements
- Ensure user context is available in chat routes

## Testing

### Manual Testing Checklist

#### Backend API
- [ ] Create new session
- [ ] Send message and receive response
- [ ] Get chat history
- [ ] Clear chat history
- [ ] Get system status
- [ ] Toggle approval mode
- [ ] Delete session
- [ ] Health check endpoint

#### Frontend UI
- [ ] Load chat interface
- [ ] Create new session via UI
- [ ] Send messages and see responses
- [ ] Switch between sessions
- [ ] Delete session via UI
- [ ] Responsive design on mobile
- [ ] Error handling for API failures

#### Integration
- [ ] Authentication flow works
- [ ] API calls use correct tokens
- [ ] Error messages display properly
- [ ] Real-time message updates
- [ ] Session persistence across page refresh

## License

[Add your license information here]

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs` endpoint
3. Check backend logs for detailed error information
4. Verify frontend console for client-side errors

---

*This system successfully transforms the CLI-based NeuralProtocol chat into a modern, scalable web application while preserving all the original functionality and extending it with multi-session support and a rich user interface.*