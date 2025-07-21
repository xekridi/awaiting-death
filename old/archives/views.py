import os

from django.db.models import F
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from .models import Archive, ClickLog


class DownloadView(View):

    def _serve_file(self, request, archive):
        zip_path = archive.zip_file.path if archive.zip_file else ""
        if not zip_path or not os.path.exists(zip_path):
            return render(request, "preview.html", {
                "archive": archive,
                "files": [],
                "file_exists": False,
            })

        response = FileResponse(
            open(zip_path, "rb"),
            as_attachment=True,
            filename=f"{archive.name}.zip",
        )
        ClickLog.objects.create(
            archive=archive,
            ip_address=request.META.get("REMOTE_ADDR", ""),
        )
        archive.download_count = F("download_count") + 1
        archive.save(update_fields=["download_count"])
        return response

    def get(self, request, code):
        archive = get_object_or_404(Archive, short_code=code, deleted_at__isnull=True)

        if not archive.ready:
            return redirect("wait", code=code)

        if archive.password:
            has_access = (
                request.session.get(f"access_{archive.id}") or
                archive.check_password(request.GET.get("password", ""))
            )
            if not has_access:
                return HttpResponseForbidden()

        if archive.expires_at and archive.expires_at < timezone.now():
            return HttpResponseForbidden()
        if archive.max_downloads and archive.download_count >= archive.max_downloads:
            return HttpResponseForbidden()

        return self._serve_file(request, archive)

    def post(self, request, code):
        archive = get_object_or_404(Archive, short_code=code, deleted_at__isnull=True)

        if not archive.ready:
            return redirect("wait", code=code)

        if archive.password and not archive.check_password(request.POST.get("password", "")):
            return HttpResponseForbidden()

        request.session[f"access_{archive.id}"] = True

        return redirect("download", code=code)
