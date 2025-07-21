import logging
import uuid

from django.urls import reverse

from ..models.archive import Archive
from ..models.file_item import FileItem
from ..tasks import build_zip
from ..utils import generate_qr_image

logger = logging.getLogger("archives.services.upload")
logger.setLevel(logging.DEBUG)

def handle_upload(form_data, user, request):
    cd = form_data
    code = uuid.uuid4().hex[:10]
    archive = Archive.objects.create(
        short_code    = code,
        name          = cd["name"],
        description   = cd.get("description", ""),
        password      = cd.get("password1", ""),
        max_downloads = cd.get("max_downloads") or 0,
        expires_at    = cd.get("expires_at"),
        owner         = user if user.is_authenticated else None,
        ready         = False,
    )
    for f in cd["files"]:
        FileItem.objects.create(archive=archive, file=f)

    task = build_zip.apply_async((archive.id,))
    archive.build_task_id = task.id
    archive.save(update_fields=["build_task_id"])

    preview_url = request.build_absolute_uri(
        reverse("download-page", args=[archive.short_code])
    )
    qr_file = generate_qr_image(preview_url)
    archive.qr_image.save(f"{archive.short_code}.png", qr_file, save=True)

    return archive
