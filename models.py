from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class ChatCreate(BaseModel):
    title: Optional[str] = "New Chat"

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Message content cannot be empty")

class MessageResponse(BaseModel):
    id: str
    chat_id: str
    role: MessageRole
    content: str
    created_at: datetime
    updated_at: datetime
    is_streaming: bool = False

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    user_id: str

    class Config:
        from_attributes = True

class ChatWithMessages(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    user_id: str
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

class StreamResponse(BaseModel):
    """Response model for streaming data"""
    type: str  # 'token', 'complete', 'error'
    content: str
    message_id: Optional[str] = None

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None 