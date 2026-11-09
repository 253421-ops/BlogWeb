"""Contraseñas (bcrypt) y tokens JWT. Los tokens llevan `iss`, `scope` y `kind` para que
las otras APIs (métricas, generador, revisión, previsualización) acepten el mismo Bearer."""
import time
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import settings

ISSUER = "devblog"
USER_SCOPES = ("posts:read posts:write categories:read categories:write builds:read builds:write "
               "metrics:read reviews:write previews:write")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode()[:72], password_hash.encode())


def _sign(sub: str, scope: str, kind: str, seconds: int) -> str:
    now = int(time.time())
    return jwt.encode({"sub": sub, "scope": scope, "kind": kind, "iss": ISSUER, "iat": now, "exp": now + seconds},
                      settings.secret_key, algorithm="HS256")


def create_token(user_id: int) -> str:
    return _sign(str(user_id), USER_SCOPES, "user", settings.access_token_minutes * 60)


def service_token(scope: str) -> str:
    """Token corto para que el CMS llame a otra API."""
    return _sign("cms", scope, "service", 60)


def decode_token(token: str) -> str:
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"], issuer=ISSUER)["sub"]
