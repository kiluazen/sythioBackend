#!/usr/bin/env python3
"""
Startup script for Jarvis Chat API
"""

import uvicorn
from config import settings

def main():
    """Main entry point"""
    print("🚀 Starting Jarvis Chat API Server...")
    print(f"📡 Server will be available at: http://{settings.HOST}:{settings.PORT}")
    print(f"📖 API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"🔧 Debug Mode: {settings.DEBUG}")
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )

if __name__ == "__main__":
    main() 