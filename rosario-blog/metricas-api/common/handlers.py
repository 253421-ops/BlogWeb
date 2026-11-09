"""Manejadores globales de errores. Aquí vive el "traductor" de los errores de Pydantic
(en inglés y con otra forma) al formato de error del contrato, en español."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from common.errors import AppError

log = logging.getLogger("cms-api")

_SLUG_MSG = "solo minúsculas, números y guiones (sin guion al inicio/final ni dobles)"


def _translate(err: dict) -> str:
    kind, ctx, field = err["type"], err.get("ctx") or {}, str(err["loc"][-1]) if err["loc"] else ""
    if kind == "missing":
        return "es obligatorio"
    if kind == "string_too_short":
        return f"debe tener al menos {ctx.get('min_length')} caracteres"
    if kind == "string_too_long":
        return f"debe tener como máximo {ctx.get('max_length')} caracteres"
    if kind == "string_pattern_mismatch":
        return _SLUG_MSG if field in ("slug",) else "formato no válido"
    if kind == "extra_forbidden":
        return "campo no permitido o de solo lectura"
    if kind in ("uuid_parsing", "uuid_type"):
        return "debe ser un UUID"
    if kind == "too_long":
        return f"máximo {ctx.get('max_length')} elementos"
    if kind in ("string_type", "list_type", "bool_type"):
        return "tiene un tipo de dato incorrecto"
    if kind in ("datetime_parsing", "datetime_type", "datetime_from_date_parsing"):
        return "debe ser fecha ISO 8601 con zona horaria (ej. 2026-12-01T15:00:00Z)"
    if kind == "int_parsing":
        return "debe ser un número entero"
    if kind in ("greater_than_equal", "less_than_equal"):
        return f"fuera de rango (mín. {ctx.get('ge', '-')}, máx. {ctx.get('le', '-')})"
    if kind == "enum":
        return f"valor no válido; opciones: {ctx.get('expected')}"
    if kind == "value_error":
        return err["msg"].removeprefix("Value error, ")
    return err["msg"]


def _path(err: dict) -> str:
    parts = [str(p) for p in err["loc"][1:]]  # se omite "body" / "query" / "path"
    return ".".join(parts) or "solicitud"


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status, content={"error": exc.code, "message": exc.message, "details": exc.details}
                            if exc.details else {"error": exc.code, "message": exc.message})

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        if any(e["type"] == "json_invalid" for e in errors):
            return JSONResponse(status_code=400, content={"error": "bad_request", "message": "JSON inválido"})
        details = [f"{_path(e)}: {_translate(e)}" for e in errors]
        return JSONResponse(status_code=422, content={"error": "unprocessable", "message": "Datos no válidos", "details": details})

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
        msg = f"Ruta no encontrada: {request.method} {request.url.path}" if exc.status_code == 404 else str(exc.detail)
        return JSONResponse(status_code=exc.status_code, content={"error": code, "message": msg})

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception):
        log.exception("Error inesperado")
        return JSONResponse(status_code=500, content={"error": "internal_error", "message": "Error interno del servidor"})
