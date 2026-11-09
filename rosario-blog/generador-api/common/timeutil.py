"""Fechas: siempre UTC y en formato ISO 8601 con milisegundos (2026-10-20T15:00:00.000Z)."""
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
