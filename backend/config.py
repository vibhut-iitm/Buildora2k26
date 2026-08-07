import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)
load_dotenv()

# Default Mode
DB_MODE = os.getenv("DB_MODE", "supabase")

# Supabase Credentials (loaded from environment or .env file)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")

# Frontend URL for CORS
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")
