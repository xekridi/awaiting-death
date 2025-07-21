import logging
import os
import uuid
import zipfile

from celery.result import AsyncResult
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, FormView, ListView, TemplateView

from .business.stats import get_downloads_by_day, get_top_referers
from .forms import UploadForm
from .models import Archive, FileItem
from .tasks import build_zip
from .utils import generate_qr_image

logger = logging.getLogger("archives.views_user")
logger.setLevel(logging.DEBUG)

class HomePage(TemplateView):
    template_name = "home.html"


class UploadView(FormView):
    template_name = "upload.html"
    form_class = UploadForm

    def form_valid(self, form):
        cd   = form.cleaned_data
        code = uuid.uuid4().hex[:10]

        archive = Archive.objects.create(
            short_code   = code,
            name         = cd.get("name"),
            description  = cd.get("description", ""),
            password     = cd.get("password1", ""),
            max_downloads= cd.get("max_downloads") or 0,
            expires_at   = cd.get("expires_at"),
            owner        = self.request.user if self.request.user.is_authenticated else None,
            ready        = False,
        )
        for f in cd["files"]:
            FileItem.objects.create(archive=archive, file=f)

        task = build_zip.apply_async((archive.id,))
        archive.build_task_id = task.id
        archive.save(update_fields=["build_task_id"])
        preview_url = self.request.build_absolute_uri(reverse("download-page", args=[archive.short_code]))
        qr_file = generate_qr_image(preview_url)
        archive.qr_image.save(f"{archive.short_code}.png", qr_file, save=True)
        return redirect("wait", code=code)

    def form_invalid(self, form):
        logger.debug("UPLOAD errors: %s", form.errors.as_json())
        return super().form_invalid(form)


class WaitView(TemplateView):
    template_name = "wait.html"

    def get_context_data(self, **kwargs):
        archive = get_object_or_404(Archive, short_code=kwargs["code"], deleted_at__isnull=True)
        return {"archive": archive}


def wait_progress(request, code):
    qs = Archive.objects.filter(short_code=code, deleted_at__isnull=True)
    if not request.user.is_authenticated:
        try:
            archive = qs.get(owner__isnull=True)
        except Archive.DoesNotExist:
            return redirect_to_login(request.get_full_path())
    else:
        archive = get_object_or_404(qs)
        if archive.owner and archive.owner != request.user:
            raise Http404()

    if archive.error:
        return JsonResponse({"state": "FAILURE", 
                             "message": archive.error, 
                             "pct": 0})

    if archive.ready:
        return JsonResponse({"state": "SUCCESS", 
                             "url": archive.get_download_url(), 
                             "pct": 100})

    if not archive.build_task_id:
        return JsonResponse({"state": "PENDING", 
                             "pct": 0})

    result = AsyncResult(archive.build_task_id)
    info   = getattr(result, "info", {}) or {}
    return JsonResponse({"state": result.state, 
                         "pct": info.get("pct", 
                                         0)})

class PreviewView(TemplateView):
    template_name = "preview.html"

    def get(self, request, code):
        archive = get_object_or_404(Archive, short_code=code, deleted_at__isnull=True)

        has_access = (not archive.password) \
            or request.session.get(f"access_{archive.id}")

        files, exists = [], False
        if archive.ready and archive.zip_file and os.path.exists(archive.zip_file.path):
            exists = True
            with zipfile.ZipFile(archive.zip_file.path) as zf:
                files = zf.namelist()

        return render(request, self.template_name, {
            "archive": archive,
            "files": files,
            "file_exists": exists,
            "has_access": has_access,
        })

    def post(self, request, code):
        archive = get_object_or_404(Archive, short_code=code, deleted_at__isnull=True)
        if archive.check_password(request.POST.get("password", "")):
            request.session[f"access_{archive.id}"] = True
        return redirect("download-page", code=code)


class DownloadPageView(LoginRequiredMixin, DetailView):
    model = Archive
    template_name = "detail.html"
    context_object_name = "archive"
    slug_field = "short_code"
    slug_url_kwarg = "code"
    login_url = reverse_lazy("login")


class DashboardView(LoginRequiredMixin, ListView):
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
    slug_url_kwarg = "code"
    login_url = reverse_lazy("login")

    def get_queryset(self):
        return self.request.user.archives.filter(deleted_at__isnull=True)

    def get_context_data(self, **kw):
        ctx = super().get_context_data(**kw)
        ctx["code"] = self.object.short_code
        ctx["by_day"] = get_downloads_by_day(self.object.short_code)
        ctx["top_referers"] = get_top_referers(self.object.short_code)
        return ctx
