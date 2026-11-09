"""Errores de negocio. Las capas internas los lanzan; main.py los traduce a HTTP con el formato
{"error", "message", "details"} del contrato."""


class AppError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, detail: str | dict, headers: dict | None = None):
        super().__init__(str(detail))
        self.detail = detail
        self.headers = headers


class NotFoundError(AppError):
    status_code, code = 404, "not_found"


class ConflictError(AppError):
    status_code, code = 409, "conflict"


class InvalidDataError(AppError):
    status_code, code = 422, "unprocessable"


class PayloadTooLargeError(AppError):
    status_code, code = 413, "payload_too_large"


class UnsupportedMediaError(AppError):
    status_code, code = 415, "unsupported_media_type"


class ExternalServiceError(AppError):
    status_code, code = 502, "bad_gateway"


class UnauthorizedError(AppError):
    status_code, code = 401, "unauthorized"

    def __init__(self, detail: str = "No autenticado"):
        super().__init__(detail, headers={"WWW-Authenticate": "Bearer"})
