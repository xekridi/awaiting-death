import os
import uuid
import zipfile
import logging
from pathlib import Path

from celery import states
from celery.exceptions import Ignore
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files import File

from .models import Archive, FileItem
from config.celery import app

logger = logging.getLogger(__name__)


@app.task(bind=True, autoretry_for=(Exception,), max_retries=3, retry_backoff=True, retry_backoff_max=600)
def build_zip(self, archive_id):
    arch = Archive.objects.select_for_update().get(pk=archive_id)

    if not arch.build_task_id:
        Archive.objects.filter(pk=archive_id).update(build_task_id=self.request.id)

    if arch.zip_file and default_storage.exists(arch.zip_file.name):
        self.update_state(state=states.SUCCESS, meta={"pct": 100})
        return arch.zip_file.name

    zip_dir = Path(settings.MEDIA_ROOT) / "zips"
    zip_dir.mkdir(parents=True, exist_ok=True)
    zip_name = f"{arch.idempotency_key}.zip"
    tmp_path = zip_dir / zip_name

    files_qs = FileItem.objects.filter(archive=arch)
    total = files_qs.count() or 1

    self.update_state(state="PROGRESS", meta={"pct": 5})

    with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, item in enumerate(files_qs, start=1):
            zf.write(item.file.path, item.file.name)
            pct = 5 + int(idx * 85 / total)
            self.update_state(state="PROGRESS", meta={"pct": pct})

    with open(tmp_path, "rb") as fp:
        arch.zip_file.save(f"zips/{zip_name}", File(fp))

    arch.ready = True
    arch.error = None
    arch.save(update_fields=["zip_file", "ready", "error"])

    self.update_state(state=states.SUCCESS, meta={"pct": 100})
    return arch.zip_file.name


@build_zip.on_failure
def build_zip_failed(exc, task_id, args, kwargs, einfo):
    archive_id = args[0] if args else kwargs.get("archive_id")
    logger.exception("build_zip failed for %s", archive_id)
    Archive.objects.filter(pk=archive_id).update(error=str(exc))
    raise Ignore()


@app.task(bind=True)
def cleanup_expired_archives(self):
    now = timezone.now()
    for arch in Archive.objects.filter(expires_at__lt=now):
        if arch.zip_file:
            default_storage.delete(arch.zip_file.name)
        FileItem.objects.filter(archive=arch).delete()
        arch.delete()
