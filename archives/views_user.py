import os
import uuid
import logging

from django.conf import settings
from django.db.models import F
from django.db import IntegrityError
from django.http import Http404, HttpResponseForbidden, FileResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib.auth.views import redirect_to_login
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, FormView, ListView, DetailView
from celery.result import AsyncResult
from django.core.files.uploadedfile import UploadedFile

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from rest_framework.views import APIView
from rest_framework.response import Response

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
    form_class    = UploadForm

    def post(self, request, *args, **kwargs):
        logger.debug("=== UploadView.POST start ===")
        logger.debug("Headers: %s", dict(request.headers))
        logger.debug("POST keys: %s", list(request.POST.keys()))
        logger.debug("FILES keys: %s", list(request.FILES.keys()))

        
        uploaded = request.POST.get("files")
        if not request.FILES.getlist("files") and isinstance(uploaded, UploadedFile):
            request.FILES.setlist("files", [uploaded])
            logger.debug("Moved UploadedFile from POST to FILES")

        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        logger.debug("=== UploadView.form_invalid ===")
        logger.debug("Form errors: %s", form.errors.as_json())
        return super().form_invalid(form)

    def form_valid(self, form):
        cd   = form.cleaned_data
        code = uuid.uuid4().hex[:10]
        logger.debug("=== UploadView.form_valid === code=%s", code)

        archive = Archive.objects.create(
            short_code    = code,
            description   = cd.get("description") or "",
            password      = cd.get("password1") or "",
            max_downloads = cd.get("max_downloads") or 0,
            expires_at    = cd.get("expires_at"),
            owner         = self.request.user if self.request.user.is_authenticated else None,
            ready         = False,
        )
        logger.debug("Archive created id=%s owner=%r", archive.id, archive.owner)

        files = self.request.FILES.getlist("files")
        logger.debug("Saving %d files: %s", len(files), [f.name for f in files])
        for f in files:
            FileItem.objects.create(archive=archive, file=f)

        task = build_zip.apply_async((archive.id,))
        archive.build_task_id = task.id
        archive.save(update_fields=["build_task_id"])
        logger.debug("Triggered build_zip task_id=%s", task.id)

        wait_url = reverse("wait", args=[archive.short_code])
        logger.debug("Redirecting to %s", wait_url)
        return redirect(wait_url)


class WaitView(TemplateView):
    template_name = "wait.html"

    def get_context_data(self, **kwargs):
        code = kwargs.get("code")
        logger.debug("=== WaitView.get_context_data === code=%s", code)
        archive = get_object_or_404(Archive, short_code=code, deleted_at__isnull=True)
        logger.debug("Archive ready=%s", archive.ready)
        return {"archive": archive}


def wait_progress(request, code):
    logger.debug("=== wait_progress === code=%s user=%r", code, request.user)
    archive = get_object_or_404(Archive, short_code=code, deleted_at__isnull=True)

    if archive.owner:
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            logger.debug("wait_progress: redirect to login")
            return redirect_to_login(request.get_full_path())
        if request.user != archive.owner:
            logger.debug("wait_progress: wrong owner -> 404")
            raise Http404()

    if archive.ready:
        return JsonResponse({"state": "SUCCESS", "pct": 100, "url": archive.get_download_url()})
    if archive.error:
        return JsonResponse({"state": "FAILURE", "pct": 0, "message": archive.error})
    if not archive.build_task_id:
        return JsonResponse({"state": "PENDING", "pct": 0})

    res = AsyncResult(archive.build_task_id)
    logger.debug("Celery state=%s info=%r", res.state, res.info)

    if res.failed():
        info = res.info or {}
        msg = info.get("exc") if isinstance(info, dict) else str(info)
        return JsonResponse({"state": "FAILURE", "pct": 0, "message": msg})

    pct = (res.info or {}).get("pct", 0)
    if res.state == "SUCCESS":
        if not archive.ready:
            archive.ready = True
            archive.save(update_fields=["ready"])
        return JsonResponse({"state": "SUCCESS", "pct": 100, "url": archive.get_download_url()})

    return JsonResponse({"state": res.state, "pct": pct})


class DownloadView(View):
    def get(self, request, code):
        arch = get_object_or_404(Archive, short_code=code, ready=True)
        if arch.expires_at and arch.expires_at < timezone.now():
            raise Http404
        if arch.password and request.GET.get("password") != arch.password:
            return HttpResponseForbidden()
        if arch.max_downloads and arch.download_count >= arch.max_downloads:
            return HttpResponseForbidden()
        Archive.objects.filter(pk=arch.pk).update(download_count=F("download_count") + 1)
        ClickLog.objects.create(
            archive=arch,
            referer=request.META.get("HTTP_REFERER", ""),
            ip_address=request.META.get("REMOTE_ADDR", ""),
        )

        file_path = os.path.join(settings.MEDIA_ROOT, arch.zip_file.name)
        if not os.path.exists(file_path):
            raise Http404
        return FileResponse(open(file_path, "rb"), as_attachment=True, filename=os.path.basename(file_path))



class DashboardView(LoginRequiredMixin, ListView):
    model = Archive
    template_name = "dashboard.html"
    context_object_name = "archives"
    login_url = reverse_lazy("login")

    def get_queryset(self):
        return self.request.user.archives.filter(deleted_at__isnull=True)


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
    login_url = "login"
    
    def get_queryset(self):
        return self.request.user.archives.all()

class StatsAPIView(APIView):
    def get(self, request, short_code):
        return Response({
            "by_day": get_downloads_by_day(short_code),
            "top_referers": get_top_referers(short_code),
        })
