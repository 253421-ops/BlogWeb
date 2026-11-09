"""MODELO: tabla `events` (una anotación de interacción; sin IP ni User-Agent completo)."""
from sqlalchemy import Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "events"
    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)     # lo genera el navegador: un reintento no duplica
    type: Mapped[str] = mapped_column(String(20))                           # page_view|scroll_depth|time_on_page|link_click
    session_id: Mapped[str] = mapped_column(String(36))
    visitor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    path: Mapped[str] = mapped_column(String(300))
    post_slug: Mapped[str | None] = mapped_column(String(80), nullable=True)
    referrer_host: Mapped[str | None] = mapped_column(String(120), nullable=True)
    target_host: Mapped[str | None] = mapped_column(String(120), nullable=True)
    value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    device_class: Mapped[str] = mapped_column(String(10))                   # desktop|mobile|tablet
    received_at: Mapped[str] = mapped_column(String(30), index=True)        # hora del SERVIDOR
    __table_args__ = (Index("ix_events_type_time", "type", "received_at"),)
