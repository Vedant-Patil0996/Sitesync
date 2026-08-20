from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # PostgreSQL (direct + pooled)
    DATABASE_URL: str
    DIRECT_URL: str = ""

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # Groq AI (added later)
    GROQ_API_KEY: str = ""

    # Weather (added later)
    OPENWEATHER_API_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
