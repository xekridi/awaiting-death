import celery.result

def _eager_result_new(cls, *args, **kwargs):
    return object.__new__(cls)

celery.result.EagerResult.__new__ = classmethod(_eager_result_new)

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
from django.db import transaction


from .models import Archive, FileItem
from config.celery import app

logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=600,
)
def build_zip(self, archive_id):
    with transaction.atomic():
        arch = Archive.objects.select_for_update().get(pk=archive_id)

        if not arch.build_task_id:
            arch.build_task_id = self.request.id
            arch.save(update_fields=["build_task_id"])

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

    try:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, item in enumerate(files_qs, start=1):
                zf.write(item.file.path, item.file.name)
                pct = 5 + int(idx * 85 / total)
                self.update_state(state="PROGRESS", meta={"pct": pct})

        rel_path = f"zips/{zip_name}"
        with open(tmp_path, "rb") as fp:
            default_storage.save(rel_path, File(fp))

        with transaction.atomic():
            arch = Archive.objects.select_for_update().get(pk=archive_id)
            arch.zip_file.name = rel_path
            arch.ready = True
            arch.error = None
            arch.save(update_fields=["zip_file", "ready", "error"])

        self.update_state(state=states.SUCCESS, meta={"pct": 100})
        return rel_path

    except Exception as exc:
        logger.exception("build_zip failed for archive %s", archive_id)
        with transaction.atomic():
            arch = Archive.objects.select_for_update().get(pk=archive_id)
            arch.error = str(exc)
            arch.save(update_fields=["error"])
        self.update_state(state=states.FAILURE, meta={"exc": str(exc)})
        raise Ignore()


@app.task(bind=True)
def cleanup_expired_archives(self):
    now = timezone.now()
    for arch in Archive.objects.filter(expires_at__lt=now):
        if arch.zip_file:
            default_storage.delete(arch.zip_file.name)
        FileItem.objects.filter(archive=arch).delete()
        arch.delete()
