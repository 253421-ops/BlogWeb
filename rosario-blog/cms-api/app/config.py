from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # SQLite por defecto (funciona sin instalar nada). PostgreSQL: ver docker-compose.yml y .env.example
    database_url: str = "sqlite:///./cms.db"
    # La MISMA clave en los 6 servicios (en los demás se llama JWT_SECRET; aquí vale SECRET_KEY o JWT_SECRET)
    secret_key: str = Field("dev-secret-solo-para-desarrollo-cambialo", validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET"))
    access_token_minutes: int = 480
    admin_email: str = "admin@example.com"
    admin_password: str = "admin123"
    builder_url: str = "http://127.0.0.1:8013"   # API del generador (vacío = build simulado)
    metrics_url: str = "http://127.0.0.1:8012"   # API de métricas (vacío = métricas simuladas)
    upload_dir: str = "uploads"
    cors_origins: str = "http://127.0.0.1:8010,http://localhost:8010,http://localhost:3000"


settings = Settings()
