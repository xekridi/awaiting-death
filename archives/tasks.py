import os
import uuid
import zipfile
import logging
from celery import Task, states
from celery.exceptions import Ignore
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files import File

from .models import Archive, FileItem
from config.celery import app

logger = logging.getLogger(__name__)

class BuildZipTask(Task):
    name = "archives.tasks.build_zip"
    autoretry_for = (Exception,)
    max_retries = 3
    retry_backoff = True
    retry_backoff_max = 600

    def apply_async(self, args=None, kwargs=None, **opts):
        if args is None:
            args = ()
        res = super().apply_async(args=args, kwargs=kwargs, **opts)
        if len(args) >= 1:
            try:
                Archive.objects.filter(pk=args[0]).update(build_task_id=res.id)
            except Exception:
                pass
        return res

    def run(self, *args, **kwargs):
        if len(args) >= 2:
            archive_id = args[1]
        elif len(args) == 1:
            archive_id = args[0]
        else:
            raise ValueError("Archive ID not provided")

        arch = Archive.objects.get(pk=archive_id)

        if arch.ready and arch.zip_file and default_storage.exists(arch.zip_file.name):
            return arch.zip_file.name

        zip_dir = os.path.join(settings.MEDIA_ROOT, "zips")
        os.makedirs(zip_dir, exist_ok=True)
        zip_name = f"{uuid.uuid4()}.zip"
        tmp_path = os.path.join(zip_dir, zip_name)

        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in FileItem.objects.filter(archive=arch):
                zf.write(item.file.path, item.file.name)

        with open(tmp_path, "rb") as fp:
            arch.zip_file.save(f"zips/{zip_name}", File(fp))

        arch.ready = True
        arch.error = None
        arch.save(update_fields=["zip_file", "ready", "error"])
        return arch.zip_file.name

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.exception("build_zip failed for %s", args)
        Archive.objects.filter(pk=args[0]).update(error=str(exc))
        super().on_failure(exc, task_id, args, kwargs, einfo)

build_zip = app.register_task(BuildZipTask())

@app.task
def cleanup_expired_archives():
    now = timezone.now()
    for arch in Archive.objects.filter(expires_at__lt=now):
        if arch.zip_file:
            default_storage.delete(arch.zip_file.name)
        FileItem.objects.filter(archive=arch).delete()
        arch.delete()
