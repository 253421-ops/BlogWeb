"""SERVICE de compilaciones: pide, ejecuta (una a la vez) y registra cada compilación. COALESCENCIA: si ya hay una esperando, no crea otra."""
import json
import threading
import time
from pathlib import Path

from generador.models import BuildJob
from generador.repository.builds_repository import BuildsRepository
from generador.services.site_builder import BuildError, from_bundle, render_site, write_site
from common.errors import not_found
from common.ids import uuid7
from common.timeutil import to_iso, utcnow

BUILD_LOCK = threading.Lock()


def _bundle_file(settings) -> Path:
    return Path(settings.output_dir).resolve().parent / "last_bundle.json"


def save_last_bundle(settings, bundle: dict) -> None:
    f = _bundle_file(settings)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")


def load_last_bundle(settings) -> dict | None:
    f = _bundle_file(settings)
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def run_job(app, build_id: str) -> None:
    with BUILD_LOCK, app.state.session_factory() as session:
        repo = BuildsRepository(session)
        job, t0 = repo.get(build_id), time.time()
        job.status, job.started_at = "RUNNING", to_iso(utcnow())
        repo.save()
        try:
            bundle = app.state.bundles.pop(build_id, None) or load_last_bundle(app.state.settings)
            if bundle is None:
                raise BuildError("NO_CONTENT", "Aún no hay contenido: pide la compilación desde el CMS (POST /api/build)")
            save_last_bundle(app.state.settings, bundle)
            posts, categories, pages = from_bundle(bundle)
            files = render_site(posts, categories, app.state.settings, pages)
            write_site(files, app.state.settings.output_dir)
            job.status, job.pages_generated = "SUCCEEDED", sum(1 for f in files if f.endswith(".html"))
        except BuildError as err:
            job.status, job.error_code, job.error_message = "FAILED", err.code, str(err)[:500]
        except Exception as err:  # noqa: BLE001
            job.status, job.error_code, job.error_message = "FAILED", "UNEXPECTED", str(err)[:500]
        job.finished_at, job.duration_ms = to_iso(utcnow()), round((time.time() - t0) * 1000)
        repo.save()


class BuildsService:
    def __init__(self, repo: BuildsRepository, app):
        self.repo, self.app = repo, app

    def enqueue(self, reason: str, bundle: dict | None) -> tuple[BuildJob, bool]:
        queued = self.repo.find_queued()
        if queued:                                    # coalescencia: la compilación en espera usará el contenido más nuevo
            if bundle is not None:
                self.app.state.bundles[queued.build_id] = bundle
            return queued, True
        job = BuildJob(build_id=uuid7(), status="QUEUED", reason=reason, post_id=None, created_at=to_iso(utcnow()))
        self.repo.add(job)
        if bundle is not None:
            self.app.state.bundles[job.build_id] = bundle
        if self.app.state.sync_builds:
            run_job(self.app, job.build_id)
        else:
            threading.Thread(target=run_job, args=(self.app, job.build_id), daemon=True).start()
        return job, False

    def get(self, build_id: str) -> BuildJob:
        job = self.repo.get(build_id)
        if not job:
            raise not_found("No existe esa compilación")
        return job

    def latest(self) -> BuildJob:
        job = self.repo.latest()
        if not job:
            raise not_found("Todavía no hay compilaciones")
        return job

    def list(self, limit: int) -> dict:
        return {"items": self.repo.list(limit)}
