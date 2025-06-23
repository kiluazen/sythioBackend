import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    
    # FastAPI Configuration
    HOST: str = os.getenv("HOST", "localhost")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # CORS Settings
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # Demo user (since we're not implementing auth)
    DEMO_USER_ID: str = "demo-user"

settings = Settings()

# Validation
if not settings.OPENAI_API_KEY:
    print("⚠️  WARNING: OPENAI_API_KEY not set in environment variables")
    print("   Please set it in your .env file or environment")
    
print(f"🔧 Config loaded:")
print(f"   Supabase URL: {settings.SUPABASE_URL}")
print(f"   Frontend URL: {settings.FRONTEND_URL}")
print(f"   Debug Mode: {settings.DEBUG}") 