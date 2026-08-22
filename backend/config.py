import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    SERVICE_KEY = os.getenv("SERVICE_KEY", "")
    PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET", "")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

settings = Settings()
