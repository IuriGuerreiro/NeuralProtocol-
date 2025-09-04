#!/usr/bin/env python3
"""
NeuralProtocol Chat API Server Runner

This script starts the FastAPI chat server with proper configuration.
"""

import uvicorn
import argparse
import sys
import os
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Run NeuralProtocol Chat API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to (default: 8000)')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload for development')
    parser.add_argument('--workers', type=int, default=1, help='Number of worker processes')
    parser.add_argument('--log-level', default='info', choices=['critical', 'error', 'warning', 'info', 'debug', 'trace'])
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    if not (current_dir / 'api' / 'chat_api.py').exists():
        print("Error: chat_api.py not found. Please run this script from the backend directory.")
        sys.exit(1)
    
    # Check for configuration files
    config_files = ["servers_config.json", "simple_servers_config.json"]
    config_found = any(Path(f).exists() for f in config_files)
    
    if not config_found:
        print("Warning: No MCP server configuration file found!")
        print("The API will work but some features may not be available.")
        print("Please create one of these files:")
        for file in config_files:
            print(f"  - {file}")
        print()
    
    print(f"🚀 Starting NeuralProtocol Chat API Server...")
    print(f"📡 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"🔄 Reload: {args.reload}")
    print(f"👥 Workers: {args.workers}")
    print(f"📝 Log Level: {args.log_level}")
    print()
    print(f"🌐 API will be available at: http://{args.host}:{args.port}")
    print(f"📋 API docs will be available at: http://{args.host}:{args.port}/docs")
    print()
    
    # Start the server
    try:
        uvicorn.run(
            "api.chat_api:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers if not args.reload else 1,  # Can't use workers with reload
            log_level=args.log_level
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()