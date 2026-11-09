"""Conexión a la base de datos SQL (SQLAlchemy): SQLite, PostgreSQL o MySQL; solo cambia la URL."""
from pathlib import Path

from fastapi import Request
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool


class UniqueViolation(Exception):
    """Una restricción UNIQUE falló (por ejemplo, un slug repetido)."""


def make_engine(url: str) -> Engine:
    backend = make_url(url)
    options: dict = {}
    if backend.get_backend_name() == "sqlite":
        options["connect_args"] = {"check_same_thread": False}
        if backend.database in (None, "", ":memory:"):
            options["poolclass"] = StaticPool  # una sola conexión compartida para que la base en memoria no se pierda
        else:
            Path(backend.database).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, **options)
    if backend.get_backend_name() == "sqlite":
        @event.listens_for(engine, "connect")
        def _fk_on(conn, _):  # SQLite no verifica llaves foráneas si no se le pide
            cur = conn.cursor(); cur.execute("PRAGMA foreign_keys=ON"); cur.close()
    return engine


def commit(session) -> None:
    try:
        session.commit()
    except IntegrityError as err:
        session.rollback()
        text = str(err.orig).lower()
        if "unique" in text or "duplicate" in text:
            raise UniqueViolation from err
        raise


def get_session(request: Request):
    """Dependencia: una sesión de base de datos por petición."""
    with request.app.state.session_factory() as session:
        yield session
