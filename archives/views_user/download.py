import os

from django.shortcuts import  redirect, render
from django.views import View
from django.views.generic import TemplateView
from django.http import FileResponse, HttpResponseForbidden, Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied, SuspiciousOperation

from ..models.archive import Archive
from ..services.download import (
    get_archive_for_download,
    mark_download_and_get_path,
    DownloadError,
)

class DownloadPageView(LoginRequiredMixin, TemplateView):
    model               = Archive
    template_name       = "detail.html"
    context_object_name = "archive"
    slug_field          = "short_code"
    slug_url_kwarg      = "code"
    login_url           = reverse_lazy("login")

class DownloadView(View):
    def get(self, request, code):
        try:
            archive = get_archive_for_download(code, request.session)
        except Exception as e:
            return HttpResponseForbidden() if isinstance(e, PermissionDenied) else Http404()
        try:
            zip_path = mark_download_and_get_path(archive, request)
        except SuspiciousOperation:
            return render(request, "preview.html", {"archive": archive, "files": [], "file_exists": False})
        return FileResponse(open(zip_path, "rb"), as_attachment=True, filename=os.path.basename(zip_path))

    def post(self, request, code):
        try:
            archive = get_archive_for_download(code, request.session, password=request.POST.get("password"))
        except PermissionDenied:
            return HttpResponseForbidden()
        except DownloadError:
            raise Http404()
        request.session[f"access_{archive.id}"] = True
        return redirect("download", code=code)
