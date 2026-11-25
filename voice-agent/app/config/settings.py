import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env if present in voice-agent root or project root
current_dir = Path(__file__).resolve().parent
env_candidates = [
    current_dir.parent.parent / ".env",
    current_dir.parent.parent.parent / ".env",
    Path(".env")
]
for env_file in env_candidates:
    if env_file.exists():
        load_dotenv(env_file)
        break

class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    
    ELEVENLABS_STT_MODEL: str = os.getenv("ELEVENLABS_STT_MODEL", "scribe_v1")
    ELEVENLABS_TTS_MODEL: str = os.getenv("ELEVENLABS_TTS_MODEL", "eleven_turbo_v2_5")
    ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel voice
    
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./medivoice.db")
    
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Kolkata")

settings = Settings()
