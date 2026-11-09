from pathlib import Path

from common.settings import CommonSettings

BASE = Path(__file__).resolve().parents[1]


class Settings(CommonSettings):
    database_url: str = f"sqlite:///{BASE / 'data' / 'generador.db'}"
    output_dir: str = str(BASE / "generated" / "site")   # el sitio compilado; este mismo servicio lo sirve en /site/
    site_base: str = "/site"
    site_title: str = "Sigo intentándolo"
    site_description: str = "Una guía honesta de alguien que sigue intentándolo."
    rate_limit_user_per_min: int = 120
    rate_limit_service_per_min: int = 300
