"""Errores HTTP "esperados". Las capas internas los lanzan y los manejadores
(core/handlers.py) los convierten en una respuesta JSON uniforme:
    {"error": "<codigo>", "message": "<texto>", "details": [...]}
"""


class AppError(Exception):
    def __init__(self, status: int, code: str, message: str, details: list[str] | None = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details


def bad_request(msg: str, details=None) -> AppError:
    return AppError(400, "bad_request", msg, details)


def unauthorized(msg: str = "No autenticado") -> AppError:
    return AppError(401, "unauthorized", msg)


def forbidden(msg: str = "Sin permiso") -> AppError:
    return AppError(403, "forbidden", msg)


def not_found(msg: str = "No existe") -> AppError:
    return AppError(404, "not_found", msg)


def conflict(msg: str, details=None) -> AppError:
    return AppError(409, "conflict", msg, details)


def unprocessable(msg: str = "Datos no válidos", details=None) -> AppError:
    return AppError(422, "unprocessable", msg, details)


def too_many_requests(msg: str = "Demasiadas peticiones, intenta más tarde") -> AppError:
    return AppError(429, "too_many_requests", msg)
