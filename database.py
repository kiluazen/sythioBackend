from supabase import create_client, Client
from typing import List, Optional, Dict, Any
from config import settings
from models import ChatResponse, MessageResponse, MessageRole
import uuid
from datetime import datetime

class DatabaseService:
    def __init__(self):
        self.supabase: Client = create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_KEY
        )
    
    async def create_chat(self, title: str = "New Chat", user_id: str = settings.DEMO_USER_ID) -> ChatResponse:
        """Create a new chat session"""
        try:
            result = self.supabase.table("chats").insert({
                "title": title,
                "user_id": user_id
            }).execute()
            
            if result.data:
                return ChatResponse(**result.data[0])
            else:
                raise Exception("Failed to create chat")
                
        except Exception as e:
            print(f"Error creating chat: {e}")
            raise
    
    async def get_chats(self, user_id: str = settings.DEMO_USER_ID) -> List[ChatResponse]:
        """Get all chats for a user that have at least one message, ordered by most recent activity"""
        try:
            # First get all chats
            result = self.supabase.table("chats")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("updated_at", desc=True)\
                .limit(50)\
                .execute()
            
            # Filter out chats with no messages - more efficient batch approach
            chats_with_messages = []
            for chat_data in result.data:
                # Check if this chat has any messages
                messages_count = self.supabase.table("messages")\
                    .select("id", count="exact")\
                    .eq("chat_id", chat_data["id"])\
                    .execute()
                
                # Only include chats that have at least one message
                if messages_count.count and messages_count.count > 0:
                    chats_with_messages.append(ChatResponse(**chat_data))
            
            return chats_with_messages
            
        except Exception as e:
            print(f"Error fetching chats: {e}")
            raise
    
    async def get_chat(self, chat_id: str, user_id: str = settings.DEMO_USER_ID) -> Optional[ChatResponse]:
        """Get a specific chat by ID"""
        try:
            result = self.supabase.table("chats")\
                .select("*")\
                .eq("id", chat_id)\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            
            if result.data:
                return ChatResponse(**result.data)
            return None
            
        except Exception as e:
            print(f"Error fetching chat {chat_id}: {e}")
            return None
    
    async def get_messages(self, chat_id: str) -> List[MessageResponse]:
        """Get all messages for a chat, ordered chronologically"""
        try:
            result = self.supabase.table("messages")\
                .select("*")\
                .eq("chat_id", chat_id)\
                .order("created_at", desc=False)\
                .execute()
            
            return [MessageResponse(**message) for message in result.data]
            
        except Exception as e:
            print(f"Error fetching messages for chat {chat_id}: {e}")
            raise
    
    async def create_message(self, chat_id: str, role: MessageRole, content: str, is_streaming: bool = False) -> MessageResponse:
        """Create a new message in a chat"""
        try:
            result = self.supabase.table("messages").insert({
                "chat_id": chat_id,
                "role": role.value,
                "content": content,
                "is_streaming": is_streaming
            }).execute()
            
            if result.data:
                return MessageResponse(**result.data[0])
            else:
                raise Exception("Failed to create message")
                
        except Exception as e:
            print(f"Error creating message: {e}")
            raise
    
    async def update_message_content(self, message_id: str, content: str, is_streaming: bool = None) -> MessageResponse:
        """Update message content (used for streaming)"""
        try:
            update_data = {"content": content}
            if is_streaming is not None:
                update_data["is_streaming"] = is_streaming
            
            result = self.supabase.table("messages")\
                .update(update_data)\
                .eq("id", message_id)\
                .execute()
            
            if result.data:
                return MessageResponse(**result.data[0])
            else:
                raise Exception("Failed to update message")
                
        except Exception as e:
            print(f"Error updating message {message_id}: {e}")
            raise
    
    async def update_chat_title(self, chat_id: str, title: str) -> ChatResponse:
        """Update chat title (useful for auto-generating titles from first message)"""
        try:
            result = self.supabase.table("chats")\
                .update({"title": title})\
                .eq("id", chat_id)\
                .execute()
            
            if result.data:
                return ChatResponse(**result.data[0])
            else:
                raise Exception("Failed to update chat title")
                
        except Exception as e:
            print(f"Error updating chat title {chat_id}: {e}")
            raise
    
    async def delete_chat(self, chat_id: str, user_id: str = settings.DEMO_USER_ID) -> bool:
        """Delete a chat and all its messages (CASCADE will handle messages)"""
        try:
            result = self.supabase.table("chats")\
                .delete()\
                .eq("id", chat_id)\
                .eq("user_id", user_id)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error deleting chat {chat_id}: {e}")
            return False

# Singleton instance
db = DatabaseService() 