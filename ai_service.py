from openai import AsyncOpenAI
from typing import List, Dict, AsyncGenerator, Any
from config import settings
from models import MessageResponse, MessageRole
import asyncio

class AIService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required")
        
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY
        )
        
        # System prompt for Jarvis Assistant
        self.system_prompt = {
            "role": "system",
            "content": """You are Jarvis, an intelligent AI assistant created by SynthioLabs. You are helpful, knowledgeable, and friendly. 

Key traits:
- Provide accurate, helpful responses
- Be concise but thorough when needed
- Ask clarifying questions when context is unclear
- Maintain a professional yet approachable tone
- Focus on practical, actionable advice

You excel at programming, technology discussions, problem-solving, and general knowledge queries. Always strive to be helpful while being honest about your limitations."""
        }
    
    def _prepare_messages_for_openai(self, chat_messages: List[MessageResponse]) -> List[Dict[str, str]]:
        """Convert chat messages to OpenAI format"""
        openai_messages = [self.system_prompt]
        
        for message in chat_messages:
            openai_messages.append({
                "role": message.role.value,
                "content": message.content
            })
        
        return openai_messages
    
    async def generate_streaming_response(
        self, 
        chat_messages: List[MessageResponse], 
        user_message: str
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from OpenAI"""
        try:
            # Prepare messages including the new user message
            messages = self._prepare_messages_for_openai(chat_messages)
            messages.append({"role": "user", "content": user_message})
            
            # Create streaming completion
            stream = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            print(f"Error in streaming AI response: {e}")
            yield f"I apologize, but I'm experiencing some technical difficulties right now. Error: {str(e)}"
    
    async def generate_chat_title(self, first_message: str) -> str:
        """Generate a concise title for the chat based on the first message"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Generate a short, descriptive title (max 6 words) for a chat conversation based on the user's first message. Be concise and capture the main topic."
                    },
                    {
                        "role": "user",
                        "content": f"First message: {first_message}"
                    }
                ],
                max_tokens=20,
                temperature=0.3
            )
            
            title = response.choices[0].message.content.strip()
            # Remove quotes if present
            title = title.strip('"\'')
            
            return title if title else "New Chat"
            
        except Exception as e:
            print(f"Error generating chat title: {e}")
            return "New Chat"

# Singleton instance
ai_service = AIService() if settings.OPENAI_API_KEY else None

def get_ai_service() -> AIService:
    """Get AI service instance with proper error handling"""
    if ai_service is None:
        raise ValueError("AI service not available - OpenAI API key not configured")
    return ai_service 