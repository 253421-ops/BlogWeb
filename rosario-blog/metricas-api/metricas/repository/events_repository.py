"""REPOSITORY de eventos: inserciones y agregaciones SQL (portables entre SQLite, PostgreSQL y MySQL)."""
from __future__ import annotations

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from metricas.models import Event
from common.db import commit


class EventsRepository:
    def __init__(self, session: Session):
        self.s = session

    def add_new(self, events: list[Event]) -> int:
        """Guarda solo los event_id que no existen (un reintento no duplica)."""
        stored = 0
        for e in events:
            if self.s.get(Event, e.event_id) is None:
                self.s.add(e); stored += 1
        commit(self.s)
        return stored

    @staticmethod
    def _range(start, end, *extra):
        return (Event.received_at >= start, Event.received_at < end, *extra)

    def totals(self, start, end):
        c = self._range(start, end, Event.type == "page_view")
        return self.s.execute(select(func.count(), func.count(distinct(Event.visitor_id)), func.count(distinct(Event.session_id))).where(*c)).one()

    def avg_dwell(self, start, end):
        return self.s.scalar(select(func.avg(Event.value)).where(*self._range(start, end, Event.type == "time_on_page")))

    def bounced(self, start, end) -> int:
        c = self._range(start, end, Event.type == "page_view")
        per_session = select(Event.session_id).where(*c).group_by(Event.session_id).having(func.count() == 1).subquery()
        return self.s.scalar(select(func.count()).select_from(per_session)) or 0

    def devices(self, start, end):
        c = self._range(start, end, Event.type == "page_view")
        return self.s.execute(select(Event.device_class, func.count()).where(*c).group_by(Event.device_class)).all()

    def referrers(self, start, end, limit=5):
        c = self._range(start, end, Event.type == "page_view", Event.referrer_host.is_not(None))
        return self.s.execute(select(Event.referrer_host, func.count().label("n")).where(*c).group_by(Event.referrer_host).order_by(func.count().desc()).limit(limit)).all()

    def top_pages(self, start, end, limit):
        c = self._range(start, end, Event.type == "page_view")
        return self.s.execute(select(Event.path, Event.post_slug, func.count().label("views"), func.count(distinct(Event.session_id))).where(*c)
                              .group_by(Event.path, Event.post_slug).order_by(func.count().desc(), Event.path).limit(limit)).all()

    def dwell_by_path(self, start, end):
        return dict(self.s.execute(select(Event.path, func.avg(Event.value)).where(*self._range(start, end, Event.type == "time_on_page")).group_by(Event.path)).all())

    def per_day(self, start, end):
        day = func.substr(Event.received_at, 1, 10)
        return self.s.execute(select(day, func.count(), func.count(distinct(Event.session_id))).where(*self._range(start, end, Event.type == "page_view")).group_by(day)).all()
