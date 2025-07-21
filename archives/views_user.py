import os
import uuid
import logging
import zipfile
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.db.models import F
from django.db import IntegrityError
from django.http import Http404, HttpResponseForbidden, FileResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib.auth.views import redirect_to_login
from django.utils import timezone
from django.utils.html import escape
from django.views import View
from django.views.generic import TemplateView, FormView, ListView, DetailView
from celery.result import AsyncResult
from django.core.files.uploadedfile import UploadedFile

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from rest_framework.views import APIView
from rest_framework.response import Response

from .utils import generate_qr_image
from .forms import UploadForm
from .models import Archive, FileItem, ClickLog
from .tasks import build_zip
from .business.stats import get_downloads_by_day, get_top_referers

import logging

logger = logging.getLogger("archives.views_user")
logger.setLevel(logging.DEBUG)

class HomePage(TemplateView):
    template_name = "home.html"


class UploadView(FormView):
    template_name = "upload.html"
    form_class = UploadForm

    def form_invalid(self, form):
        logger.debug("=== UploadView.form_invalid ===")
        logger.debug("Form errors: %s", form.errors.as_json())
        return super().form_invalid(form)

    def form_valid(self, form):
        cd = form.cleaned_data
        code = uuid.uuid4().hex[:10]
        logger.debug("=== UploadView.form_valid === code=%s", code)

        archive = Archive.objects.create(
            short_code=code,
            description   = cd.get("description", ""),
            password      = cd.get("password1", ""),
            max_downloads = cd.get("max_downloads") or 0,
            expires_at    = cd.get("expires_at"),
            owner         = self.request.user if self.request.user.is_authenticated else None,
            ready         = False,
        )
        logger.debug("Archive created id=%s owner=%r", archive.id, archive.owner)

        files = cd["files"]
        logger.debug("Saving %d files: %s", len(files), [f.name for f in files])
        for f in files:
            FileItem.objects.create(archive=archive, file=f)

        task = build_zip.apply_async((archive.id,))
        archive.build_task_id = task.id
        archive.save(update_fields=["build_task_id"])
        logger.debug("Triggered build_zip task_id=%s", task.id)
        preview_url = self.request.build_absolute_uri(
            reverse("download-page", args=[archive.short_code])
        )
        qr_file = generate_qr_image(preview_url)
        archive.qr_image.save(f"{archive.short_code}.png", qr_file, save=True)
        wait_url = reverse("wait", args=[archive.short_code])
        logger.debug("Redirecting to %s", wait_url)
        return redirect(reverse("wait", args=[archive.short_code]))


class WaitView(TemplateView):
    template_name = "wait.html"

    def get_context_data(self, **kwargs):
        code = kwargs.get("code")
        logger.debug("=== WaitView.get_context_data === code=%s", code)
        archive = get_object_or_404(Archive, short_code=code, deleted_at__isnull=True)
        logger.debug("Archive ready=%s", archive.ready)
        return {"archive": archive}


def wait_progress(request, code):
    base_qs = Archive.objects.filter(short_code=code, deleted_at__isnull=True)

    if not request.user.is_authenticated:
        try:
            archive = base_qs.get(owner__isnull=True)
        except Archive.DoesNotExist:
            return redirect_to_login(request.get_full_path())
    else:
        archive = get_object_or_404(base_qs)
        if archive.owner and archive.owner != request.user:
            raise Http404()

    if archive.owner and archive.error:
        return JsonResponse({
            "state": "FAILURE",
            "pct": 0,
            "message": archive.error,
        })

    if archive.ready:
        if archive.owner:
            return JsonResponse({
                "state": "SUCCESS",
                "pct": 100,
                "url": archive.get_download_url(),
            })
        return JsonResponse({"pct": 100})

    if not archive.build_task_id:
        if archive.owner:
            return JsonResponse({"state": "PENDING", "pct": 0})
        return JsonResponse({"pct": 0})

    result = AsyncResult(archive.build_task_id)
    info = getattr(result, "info", {}) or {}
    pct = info.get("pct", 0)

    if (hasattr(result, "failed") and result.failed()) or result.state == "FAILURE":
        msg = info.get("exc") or info.get("message") or ""
        if archive.owner:
            return JsonResponse({"state": "FAILURE", "pct": 0, "message": msg})
        return JsonResponse({"pct": 0})

    if archive.owner:
        return JsonResponse({"state": result.state, "pct": pct})
    return JsonResponse({"pct": pct})

class DownloadPageView(DetailView):
    model = Archive
    template_name = "download.html"
    context_object_name = "archive"
    slug_field = "short_code"
    slug_url_kwarg = "code"

    def get_object(self, queryset=None):
        return get_object_or_404(
            Archive,
            short_code=self.kwargs["code"],
            deleted_at__isnull=True,
        )

    def _zip_members(self, arch):
        if not arch.zip_file:
            return []
        try:
            with open(Path(settings.MEDIA_ROOT) / arch.zip_file.name, "rb") as fp:
                with zipfile.ZipFile(BytesIO(fp.read())) as zf:
                    return zf.namelist()
        except FileNotFoundError:
            return []
        except zipfile.BadZipFile:
            return []

    def get_context_data(self, **ctx):
        ctx = super().get_context_data(**ctx)
        arch = ctx["archive"]
        ctx["files"]       = self._zip_members(arch)
        ctx["file_exists"] = bool(arch.zip_file and Path(settings.MEDIA_ROOT, arch.zip_file.name).exists())
        ctx["wait_needed"] = not arch.ready
        return ctx


class DownloadView(View):
    template_name = "download.html"

    def get(self, request, code):
        archive = get_object_or_404(Archive, short_code=code, ready=True)

        if archive.expires_at and archive.expires_at < timezone.now():
            return HttpResponseForbidden()

        if archive.password:
            pwd = request.GET.get("password")
            if pwd is None:
                return render(request, self.template_name, {"archive": archive})
            if not archive.check_password(pwd):
                return HttpResponseForbidden()

        if archive.max_downloads and archive.download_count >= archive.max_downloads:
            return HttpResponseForbidden()

        path = archive.zip_file.path
        if not os.path.exists(path):
            raise Http404()

        resp = FileResponse(open(path, "rb"), as_attachment=True, filename=f"{archive.name}.zip")
        archive.download_count += 1
        archive.save(update_fields=["download_count"])
        ClickLog.objects.create(
            archive=archive,
            ip=request.META.get("REMOTE_ADDR", ""),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        return resp

    def post(self, request, code):
        return self.get(request, code)


class DashboardView(LoginRequiredMixin, ListView):
    template_name = "dashboard.html"
    context_object_name = "archives"

    def get_queryset(self):
        return self.request.user.archives.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.utils import timezone
        ctx["now"] = timezone.now()
        return ctx


class ArchiveDetailView(LoginRequiredMixin, DetailView):
    model = Archive
    template_name = "detail.html"
    context_object_name = "archive"
    slug_field = "short_code"
    slug_url_kwarg = "code"
    login_url = reverse_lazy("login")

    def get_queryset(self):
        return self.request.user.archives.all()


class StatsPageView(LoginRequiredMixin, DetailView):
    model = Archive
    template_name = "stats.html"
    slug_field = "short_code"
    slug_url_kwarg = "short_code"
    login_url = reverse_lazy("login")
    
    def get_queryset(self):
        return self.request.user.archives.all()

class StatsAPIView(APIView):
    def get(self, request, short_code):
        return Response({
            "by_day": get_downloads_by_day(short_code),
            "top_referers": get_top_referers(short_code),
        })

class PreviewView(View):
    template_name = "preview.html"

    def get(self, request, code):
        archive = get_object_or_404(Archive, short_code=code)
        if not archive.ready:
            return render(request, self.template_name, {"archive": archive})
        
        zip_path = archive.zip_file.path
        if not os.path.exists(zip_path):
            return render(request, self.template_name, {
                "archive": archive,
                "files": [],
                "file_exists": False,
            })

        with zipfile.ZipFile(zip_path) as zf:
            files = zf.namelist()

        return render(request, self.template_name, {
            "archive": archive,
            "files": files,
            "file_exists": True,
        })