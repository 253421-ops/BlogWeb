"""SERVICE de métricas: filtra robots, clasifica dispositivos y calcula las métricas. No conoce HTTP ni SQL."""
import re
from datetime import datetime, timedelta, timezone

from metricas.models import Event
from metricas.repository.events_repository import EventsRepository
from common.errors import unprocessable
from common.timeutil import to_iso

BOT = re.compile(r"bot|crawl|spider|slurp|headless|lighthouse|preview", re.I)


def classify_device(ua: str) -> str:
    if re.search(r"ipad|tablet|kindle|silk", ua, re.I) or (re.search("android", ua, re.I) and not re.search("mobile", ua, re.I)):
        return "tablet"
    return "mobile" if re.search(r"mobi|iphone|android", ua, re.I) else "desktop"


def basis_points(part: int, total: int) -> int:        # 3450 = 34.50 %
    return round(part / total * 10000) if total else 0


def resolve_range(date_from: str | None, date_to: str | None, now: datetime):
    to_day = date_to or now.strftime("%Y-%m-%d")
    parse = lambda d: datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    try:
        end_dt = parse(to_day)
        from_day = date_from or (end_dt - timedelta(days=29)).strftime("%Y-%m-%d")
        start_dt = parse(from_day)
    except ValueError:
        raise unprocessable("Rango de fechas no válido", ["usa el formato AAAA-MM-DD"]) from None
    if start_dt > end_dt or (end_dt - start_dt).days > 365:
        raise unprocessable("Rango de fechas no válido", ["from no puede ser posterior a to y el máximo es 366 días"])
    return from_day, to_day, to_iso(start_dt), to_iso(end_dt + timedelta(days=1)), start_dt, end_dt


class MetricsService:
    def __init__(self, repo: EventsRepository, clock):
        self.repo, self.clock = repo, clock

    def ingest(self, events, user_agent: str) -> dict:
        if BOT.search(user_agent or ""):                # los robots se aceptan pero no se cuentan
            return {"received": len(events), "stored": 0}
        device, now = classify_device(user_agent or ""), to_iso(self.clock())
        rows = [Event(event_id=str(e.event_id), type=e.type, session_id=str(e.session_id), visitor_id=str(e.visitor_id) if e.visitor_id else None,
                      path=e.path, post_slug=e.post_slug, referrer_host=e.referrer_host, target_host=e.target_host, value=e.value,
                      device_class=device, received_at=now) for e in events]
        return {"received": len(events), "stored": self.repo.add_new(rows)}

    def overview(self, date_from, date_to) -> dict:
        f, t, s, e, *_ = resolve_range(date_from, date_to, self.clock())
        views, visitors, sessions = self.repo.totals(s, e)
        devices = {"desktop": 0, "mobile": 0, "tablet": 0, **dict(self.repo.devices(s, e))}
        dwell = self.repo.avg_dwell(s, e)
        return {"from": f, "to": t, "views_total": views, "unique_visitors": visitors, "sessions": sessions,
                "avg_dwell_time_sec": round(dwell) if dwell else 0, "bounce_rate_bp": basis_points(self.repo.bounced(s, e), sessions),
                "devices": devices, "top_referrers": [{"host": h, "views": n} for h, n in self.repo.referrers(s, e)]}

    def pages(self, date_from, date_to, limit: int) -> dict:
        f, t, s, e, *_ = resolve_range(date_from, date_to, self.clock())
        dwell = self.repo.dwell_by_path(s, e)
        items = [{"path": p, **({"post_slug": slug} if slug else {}), "views": v, "sessions": ss, "avg_dwell_time_sec": round(dwell.get(p) or 0)}
                 for p, slug, v, ss in self.repo.top_pages(s, e, limit)]
        return {"from": f, "to": t, "items": items}

    def timeseries(self, date_from, date_to) -> dict:
        f, t, s, e, start_dt, end_dt = resolve_range(date_from, date_to, self.clock())
        by_day = {d: (v, ss) for d, v, ss in self.repo.per_day(s, e)}
        days = [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end_dt - start_dt).days + 1)]
        return {"from": f, "to": t, "items": [{"day": d, "views": by_day.get(d, (0, 0))[0], "sessions": by_day.get(d, (0, 0))[1]} for d in days]}
