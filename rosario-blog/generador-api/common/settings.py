"""Configuración común a los 6 servicios (variables de entorno y un .env opcional)."""
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SECRET = "dev-secret-solo-para-desarrollo-cambialo"


class CommonSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    jwt_secret: str = ""                      # el MISMO en todos los servicios
    cors_origins: str = "http://127.0.0.1:8010,http://localhost:8010"
    # Dónde vive cada servicio (puerto 8010 = consola, como en tu referencia)
    console_url: str = "http://127.0.0.1:8010"
    cms_url: str = "http://127.0.0.1:8011"
    metrics_url: str = "http://127.0.0.1:8012"
    generator_url: str = "http://127.0.0.1:8013"
    review_url: str = "http://127.0.0.1:8014"
    preview_url: str = "http://127.0.0.1:8015"

    @model_validator(mode="after")
    def _secret(self):
        if not self.jwt_secret:
            if self.app_env == "production":
                raise ValueError("JWT_SECRET es obligatorio en producción")
            self.jwt_secret = DEV_SECRET
        elif len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET debe tener al menos 32 caracteres")
        return self

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]
