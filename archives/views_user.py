import os
import uuid
from django.conf import settings
from django.db.models import F
from django.db import IntegrityError
from django.http import Http404, HttpResponseForbidden, FileResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.views import redirect_to_login
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, FormView, ListView, DetailView
from celery.result import AsyncResult

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from rest_framework.views import APIView
from rest_framework.response import Response

from .forms import UploadForm
from .models import Archive, FileItem, ClickLog
from .tasks import build_zip
from .business.stats import get_downloads_by_day, get_top_referers

import logging

logger = logging.getLogger(__name__)

class HomePage(TemplateView):
    template_name = "home.html"


class UploadView(LoginRequiredMixin, FormView):
    template_name = "upload.html"
    form_class    = UploadForm

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        form.is_valid()
        return self.form_valid(form)

    def form_valid(self, form):
        cd = form.cleaned_data
        code = uuid.uuid4().hex[:10]
        user = self.request.user
        logger.debug(
            "UploadView.form_valid called: user=%r, is_authenticated=%s, user.id=%r",
            user, user.is_authenticated, getattr(user, "id", None)
        )
        archive = Archive.objects.create(
            short_code    = code,
            description   = cd.get("description") or "",
            password      = cd.get("password1") or "",
            max_downloads = cd.get("max_downloads") or 0,
            expires_at    = cd.get("expires_at"),
            owner         = self.request.user if self.request.user.is_authenticated else None,
            ready         = False,
        )

        files = self.request.FILES.getlist("files") or []
        for f in files:
            FileItem.objects.create(archive=archive, file=f)

        res = build_zip.apply_async((archive.id,))
        archive.build_task_id = res.id
        archive.save(update_fields=["build_task_id"])
        return redirect("wait", code=archive.short_code)


class WaitView(TemplateView):
    template_name = "wait.html"
    
    def get_context_data(self, **kwargs):
        return {"archive": get_object_or_404(
            Archive, short_code=kwargs["code"], deleted_at__isnull=True
        )}


def wait_progress(request, code):
    try:
        arch = Archive.objects.get(short_code=code, deleted_at__isnull=True)
    except Archive.DoesNotExist:
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        raise Http404

    if arch.owner is None:
        pct = (AsyncResult(arch.build_task_id).info or {}).get("pct", 0)
        return JsonResponse({"pct": pct})

    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    if arch.owner_id != request.user.id:
        raise Http404

    if arch.ready:
        return JsonResponse({
            "state": "SUCCESS",
            "pct": 100,
            "url": arch.get_download_url(),
        })
    if arch.error:
        return JsonResponse({
            "state": "FAILURE",
            "pct": 0,
            "message": arch.error,
        })
    if not arch.build_task_id:
        return JsonResponse({"state": "PENDING", "pct": 0})

    res = AsyncResult(arch.build_task_id)
    if res.failed():
        info = res.info or {}
        msg = info.get("exc") if isinstance(info, dict) and "exc" in info else str(info)
        return JsonResponse({"state": "FAILURE", "pct": 0, "message": msg})

    state = res.state
    pct   = (res.info or {}).get("pct", 0)
    if state == "SUCCESS":
        if not arch.ready:
            arch.ready = True
            arch.save(update_fields=["ready"])
        return JsonResponse({
            "state": "SUCCESS",
            "pct": 100,
            "url": arch.get_download_url(),
        })
    return JsonResponse({"state": state, "pct": pct})


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
