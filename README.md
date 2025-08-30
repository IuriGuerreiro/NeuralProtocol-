# NeuralProtocol - AI-Powered MCP Chat Platform

**NeuralProtocol** is a sophisticated AI chat application built with **Langchain**, **Pydantic**, and **Gemini 2.0 Flash**. It features intelligent conversation management with automatic summarization, preserving context while enabling unlimited conversation length.

## 🚀 Future Vision

**NeuralProtocol** is designed to evolve into a comprehensive web-based AI chat platform with:

- **Modern Web Interface**: Responsive, intuitive chat UI with real-time messaging
- **Custom REST API Backend**: Built-in API endpoints for seamless third-party integrations
- **Multi-Platform Support**: Web, mobile-responsive, and potential desktop applications
- **User Management**: Authentication, user profiles, and conversation history
- **Real-time Features**: WebSocket connections, typing indicators, and live updates

## 🔧 Current Features

### **Smart Memory Management**
- **Automatic Summarization**: Creates intelligent summaries when memory limit is reached
- **Context Preservation**: Maintains important details like names, preferences, and key points
- **Unlimited Conversations**: No conversation length restrictions
- **Memory Efficiency**: Only keeps essential information

### **AI Integration**
- **Gemini 2.0 Flash**: Google's advanced AI model for intelligent responses
- **Langchain Framework**: Latest features and best practices
- **Fallback Support**: SimpleLLM for testing without API keys

### **Conversation Management**
- **Multiple Conversations**: Support for multiple chat sessions
- **History Tracking**: Complete conversation history with smart summarization
- **Memory Status**: Real-time memory and summary information
- **Easy Commands**: Simple commands for managing conversations

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd LangchainBasedMCPClient
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env_example.txt .env
   # Edit .env with your Google API key
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

## 📱 Usage

### **Chat Commands**
- **Regular messages**: Type normally to chat with the AI
- **`quit`**: Exit the application
- **`clear`**: Clear current conversation
- **`history`**: Show conversation history
- **`status`**: Show application status
- **`memory`**: Show detailed memory information

### **Memory Management**
The system automatically:
- Tracks conversation context
- Creates summaries when memory fills up
- Preserves important information
- Maintains conversation continuity

## ⚙️ Configuration

### **Environment Variables**
- `GOOGLE_API_KEY`: Your Google API key for Gemini
- `GEMINI_MODEL`: Gemini model to use (default: gemini-2.0-flash)
- `MAX_TOKENS`: Maximum response length (default: 1000)
- `TEMPERATURE`: Response creativity (default: 0.7)
- `MEMORY_SIZE`: Messages before summarization (default: 10)

### **Memory Settings**
- **Default Memory Size**: 10 messages
- **Summary Trigger**: Automatic when limit is reached
- **Context Preservation**: Summary + last 2 messages
- **Fallback**: Last 3 messages if summarization fails

## 🏗️ Architecture

### **Core Components**
- **NeuralProtocolApp**: Main application class
- **NeuralProtocolChatManager**: Chat and conversation management
- **ConversationMemory**: Smart memory with summarization
- **Pydantic Models**: Data validation and structure

### **Technology Stack**
- **Python 3.8+**: Core runtime
- **Langchain**: AI framework integration
- **Pydantic**: Data validation and settings
- **Google Generative AI**: Gemini model integration
- **Logging**: Comprehensive logging system

## 🔌 Future Integrations

### **Plugin System**
- Modular architecture for third-party tools
- API gateway for external services
- Webhook support for real-time notifications

### **API Development**
- RESTful endpoints for chat operations
- Authentication and user management
- Real-time communication protocols

### **Web Interface**
- Modern React/Vue.js frontend
- Responsive design for all devices
- Real-time chat experience

## 📊 Performance

- **Response Time**: 0.3s - 1.5s (including summarization)
- **Memory Efficiency**: Automatic optimization
- **Scalability**: Ready for web deployment
- **Reliability**: Fallback mechanisms and error handling

## 🚧 Development Status

- **✅ Phase 1**: Core chat functionality with smart memory
- **🌐 Phase 2**: Web interface and basic API endpoints
- **🔌 Phase 3**: Plugin system and third-party integrations
- **📱 Phase 4**: Mobile optimization and advanced features
- **🏢 Phase 5**: Enterprise features and deployment tools

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for:
- Code standards
- Testing requirements
- Documentation updates
- Feature proposals

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- **Documentation**: [NeuralProtocol Docs]
- **API Reference**: [API Documentation]
- **Community**: [Discord/Forum]
- **Issues**: [GitHub Issues]

---

**NeuralProtocol** - Where AI meets protocol, creating the future of intelligent communication. 🚀

