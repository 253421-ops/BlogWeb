"""REPOSITORY de compilaciones."""
from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from generador.models import BuildJob
from common.db import commit


class BuildsRepository:
    def __init__(self, session: Session):
        self.s = session

    def add(self, job: BuildJob) -> None:
        self.s.add(job); commit(self.s)

    def save(self) -> None:
        commit(self.s)

    def get(self, build_id: str) -> BuildJob | None:
        return self.s.get(BuildJob, build_id)

    def find_queued(self) -> BuildJob | None:
        return self.s.scalars(select(BuildJob).where(BuildJob.status == "QUEUED").order_by(BuildJob.build_id).limit(1)).first()

    def latest(self) -> BuildJob | None:
        return self.s.scalars(select(BuildJob).order_by(BuildJob.build_id.desc()).limit(1)).first()

    def list(self, limit: int) -> list[BuildJob]:
        return list(self.s.scalars(select(BuildJob).order_by(BuildJob.build_id.desc()).limit(limit)))

    def fail_interrupted(self, finished_at: str) -> None:
        self.s.execute(update(BuildJob).where(BuildJob.status == "RUNNING").values(status="FAILED", finished_at=finished_at, error_code="INTERRUPTED",
                                                                                  error_message="El servicio se reinició durante la compilación"))
        commit(self.s)
