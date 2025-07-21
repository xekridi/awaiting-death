import celery.result
from config.celery import app
from .models import Archive, FileItem

def _eager_result_new(cls, *args, **kwargs):
    return object.__new__(cls)

celery.result.EagerResult.__new__ = classmethod(_eager_result_new)

import logging
import os
import uuid
import zipfile
from pathlib import Path

from celery import shared_task
from celery.exceptions import Ignore
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone



logger = logging.getLogger(__name__)


@shared_task(bind=True)
def build_zip(self, archive_id):
    if not getattr(self.request, "id", None):
        self.request.id = uuid.uuid4().hex

    with transaction.atomic():
        arch = Archive.objects.select_for_update().get(pk=archive_id)
        existing = arch.zip_file.name
        if arch.ready and existing and Path(settings.MEDIA_ROOT, existing).exists():
            self.update_state(state="SUCCESS", meta={"pct": 100})
            return existing

    files = FileItem.objects.filter(archive=arch)
    total = files.count() or 1

    zip_dir = Path(settings.MEDIA_ROOT) / "zips"
    zip_dir.mkdir(exist_ok=True, parents=True)

    filename = f"{arch.short_code}.zip"
    tmp_path = zip_dir / filename

    try:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, item in enumerate(files, start=1):
                arcname = os.path.basename(item.file.name)
                zf.write(item.file.path, arcname)
                pct = int(idx * 100 / total)
                self.update_state(state="PROGRESS", meta={"pct": pct})

        arch.zip_file.name = f"zips/{filename}"
        arch.ready = True
        arch.error = ""
        arch.save(update_fields=["zip_file", "ready", "error"])

        self.update_state(state="SUCCESS", meta={"pct": 100})
        return arch.zip_file.name

    except Exception as exc:
        arch.error = str(exc)
        arch.save(update_fields=["error"])
        self.update_state(state="FAILURE", meta={"exc": str(exc)})
        raise Ignore()


@app.task(bind=True)
def cleanup_expired_archives(self):
    now = timezone.now()
    for arch in Archive.objects.filter(expires_at__lt=now):
        if arch.zip_file:
            default_storage.delete(arch.zip_file.name)
        FileItem.objects.filter(archive=arch).delete()
        arch.delete()
