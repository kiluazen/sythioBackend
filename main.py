from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.responses import JSONResponse
from typing import List
import json
import asyncio
from contextlib import asynccontextmanager

# Local imports
from config import settings
from models import (
    ChatCreate, ChatResponse, MessageCreate, MessageResponse, 
    ChatWithMessages, ErrorResponse, MessageRole
)
from database import db
from ai_service import get_ai_service

# Startup/shutdown logic
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    print("🚀 Starting Jarvis Chat API...")
    print(f"🔧 Environment: {'Development' if settings.DEBUG else 'Production'}")
    
    # Test database connection
    try:
        chats = await db.get_chats()
        print(f"✅ Supabase connected successfully! Found {len(chats)} existing chats")
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        
    # Test AI service
    try:
        ai = get_ai_service()
        print("✅ OpenAI service initialized successfully")
    except Exception as e:
        print(f"⚠️  OpenAI service warning: {e}")
    
    yield
    
    print("👋 Shutting down Jarvis Chat API...")

# Create FastAPI app
app = FastAPI(
    title="Jarvis Chat API",
    description="A ChatGPT-like API with streaming responses for SynthioLabs interview",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Jarvis Chat API is running",
        "version": "1.0.0"
    }

# ========================================
# Chat Management Endpoints
# ========================================

@app.get("/api/chats", response_model=List[ChatResponse])
async def get_chats():
    """Get all chats for the user (demo user), ordered by most recent activity"""
    try:
        chats = await db.get_chats()
        return chats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chats: {str(e)}")

@app.post("/api/chats", response_model=ChatResponse)
async def create_chat(chat_data: ChatCreate):
    """Create a new chat session"""
    try:
        chat = await db.create_chat(title=chat_data.title or "New Chat")
        return chat
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create chat: {str(e)}")

@app.get("/api/chats/{chat_id}", response_model=ChatWithMessages)
async def get_chat_with_messages(chat_id: str):
    """Get a specific chat with all its messages"""
    try:
        # Get chat details
        chat = await db.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        # Get messages
        messages = await db.get_messages(chat_id)
        
        # Return chat with messages
        return ChatWithMessages(
            id=chat.id,
            title=chat.title,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            user_id=chat.user_id,
            messages=messages
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat: {str(e)}")

@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: str):
    """Delete a chat and all its messages"""
    try:
        success = await db.delete_chat(chat_id)
        if not success:
            raise HTTPException(status_code=404, detail="Chat not found")
        return {"message": "Chat deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete chat: {str(e)}")

# ========================================
# Message Endpoints
# ========================================

@app.get("/api/chats/{chat_id}/messages", response_model=List[MessageResponse])
async def get_messages(chat_id: str):
    """Get all messages for a specific chat"""
    try:
        # Verify chat exists
        chat = await db.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        messages = await db.get_messages(chat_id)
        return messages
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")

# Non-streaming endpoint removed - we only support streaming responses now!

# ========================================
# Streaming Endpoint (The Star of the Show!)
# ========================================

@app.post("/api/chats/{chat_id}/stream")
async def stream_message(chat_id: str, message_data: MessageCreate, background_tasks: BackgroundTasks):
    """Send a user message and stream AI response in real-time"""
    try:
        # Verify chat exists
        chat = await db.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        # Save user message
        await db.create_message(
            chat_id=chat_id,
            role=MessageRole.USER,
            content=message_data.content
        )
        
        # Create assistant message placeholder with streaming flag
        assistant_message = await db.create_message(
            chat_id=chat_id,
            role=MessageRole.ASSISTANT,
            content="",
            is_streaming=True
        )
        
        # Get existing messages for context (excluding the empty assistant message)
        existing_messages = await db.get_messages(chat_id)
        context_messages = [msg for msg in existing_messages if msg.id != assistant_message.id]
        
        async def generate_stream():
            """Generator function for streaming response"""
            try:
                ai = get_ai_service()
                accumulated_content = ""
                
                # Stream the AI response
                async for token in ai.generate_streaming_response(context_messages, message_data.content):
                    accumulated_content += token

                    
                    # Send token to client
                    chunk = f"data: {json.dumps({'type': 'token', 'content': token, 'message_id': assistant_message.id})}\n\n"
                    yield chunk
                    
                    # Small delay to ensure proper streaming (optional)
                    await asyncio.sleep(0.01)
                    
                    # Update database periodically (every 50 chars to reduce DB calls)
                    if len(accumulated_content) % 50 == 0:
                        await db.update_message_content(
                            assistant_message.id,
                            accumulated_content,
                            is_streaming=True
                        )
                
                # Final update - mark as complete
                await db.update_message_content(
                    assistant_message.id,
                    accumulated_content,
                    is_streaming=False
                )
                
                # Send completion signal
                yield f"data: {json.dumps({'type': 'complete', 'content': '', 'message_id': assistant_message.id})}\n\n"
                
            except Exception as e:
                print(f"Streaming error: {e}")
                # Send error to client
                yield f"data: {json.dumps({'type': 'error', 'content': f'Error: {str(e)}', 'message_id': assistant_message.id})}\n\n"
                
                # Update database with error
                await db.update_message_content(
                    assistant_message.id,
                    f"I apologize, but I encountered an error: {str(e)}",
                    is_streaming=False
                )
        
        # Generate title for first message (background task)
        if len(context_messages) == 1:  # First user message
            background_tasks.add_task(
                generate_and_update_title,
                chat_id,
                message_data.content
            )
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start streaming: {str(e)}")

# ========================================
# Background Tasks
# ========================================

async def generate_and_update_title(chat_id: str, first_message: str):
    """Background task to generate and update chat title"""
    try:
        ai = get_ai_service()
        title = await ai.generate_chat_title(first_message)
        await db.update_chat_title(chat_id, title)
        print(f"Updated chat {chat_id} title to: {title}")
    except Exception as e:
        print(f"Failed to update chat title: {e}")

# ========================================
# Error Handlers
# ========================================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    ) 