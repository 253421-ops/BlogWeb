"""MODELO: tabla `build_jobs` (bitácora de compilaciones)."""
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class BuildJob(Base):
    __tablename__ = "build_jobs"
    build_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(12), index=True)            # QUEUED|RUNNING|SUCCEEDED|FAILED
    reason: Mapped[str] = mapped_column(String(100))
    post_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[str] = mapped_column(String(30))
    started_at: Mapped[str | None] = mapped_column(String(30), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String(30), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pages_generated: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
