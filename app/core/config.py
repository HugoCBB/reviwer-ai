from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    google_api_key: str = os.getenv('GOOGLE_API_KEY') or ""

    github_token: str = os.getenv('GITHUB_TOKEN') or ""
    github_webhook_secret: str = os.getenv('GITHUB_SECRET') or ""

    redis_url: str = os.getenv("REDIS_URL") or "redis://localhost:6379/0"

    llm_provider: str = os.getenv("LLM_PROVIDER") or "ollama"

    gemini_model: str = "gemini-2.0-flash"

    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL") or "http://ollama:11434"
    ollama_model: str = os.getenv("OLLAMA_MODEL") or "llama3.1"

    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY") or ""
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL") or "deepseek-chat"

    llm_temperature: float = 0.0
    max_diff_tokens: int = 4000

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()