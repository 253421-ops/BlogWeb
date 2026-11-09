"""JWT Bearer (HS256) con permisos (scopes). Un token trae: sub (quién), scope ("posts:read ..."), kind ("user"|"service")."""
import time
from dataclasses import dataclass

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from common.errors import forbidden, unauthorized

ISSUER = "devblog"
bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    sub: str
    scopes: frozenset[str]
    kind: str


def sign_token(secret: str, sub: str, scope: str, kind: str = "user", expires_in: int = 3600) -> str:
    now = int(time.time())
    return jwt.encode({"sub": sub, "scope": scope, "kind": kind, "iss": ISSUER, "iat": now, "exp": now + expires_in}, secret, algorithm="HS256")


def authenticate(secret: str, credentials: HTTPAuthorizationCredentials | None) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized("Falta el token Bearer")
    try:
        p = jwt.decode(credentials.credentials, secret, algorithms=["HS256"], issuer=ISSUER, options={"require": ["exp", "iss", "sub"]})
    except jwt.PyJWTError:
        raise unauthorized("Token inválido o expirado") from None
    return Principal(p["sub"], frozenset(str(p.get("scope", "")).split()), p.get("kind", "user"))


def require_scope(scope: str):
    """Dependencia de FastAPI: exige token válido con ese permiso y aplica el límite de tráfico (si el servicio lo tiene)."""

    async def dependency(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> Principal:
        principal = authenticate(request.app.state.settings.jwt_secret, credentials)
        if scope not in principal.scopes:
            raise forbidden(f"Falta el permiso {scope}")
        limiter = getattr(request.app.state, "limiter", None)
        if limiter:
            limiter.check(principal)
        return principal

    return dependency
