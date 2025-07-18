import os
import uuid
from django.conf import settings
from django.db.models import F
from django.db import IntegrityError
from django.contrib.auth import login, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden, FileResponse, HttpResponse, JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, FormView, ListView, DetailView
from celery.result import AsyncResult

from .forms import UploadForm, SignupForm
from .models import Archive, FileItem, ClickLog
from .tasks import build_zip

User = get_user_model()


class HomePage(TemplateView):
    template_name = "home.html"


class SignupView(FormView):
    template_name = "signup.html"
    form_class = SignupForm
    success_url = "/"

    def form_valid(self, form):
        cd = form.cleaned_data
        try:
            user = User.objects.create_user(
                username=cd["username"],
                email=cd["email"],
                password=cd["password1"],
            )
        except IntegrityError:
            form.add_error("username", "Пользователь с таким именем уже существует")
            return self.form_invalid(form)
        login(self.request, user)
        return super().form_valid(form)


class CustomLoginView(LoginView):
    template_name = "login.html"


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("home")
    http_method_names = ["get", "post"]

    def get(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UploadView(FormView):
    template_name = "upload.html"
    form_class = UploadForm

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        form.is_valid()
        return self.form_valid(form)

    def form_valid(self, form):
        cd = form.cleaned_data
        code = uuid.uuid4().hex[:10]
        archive = Archive.objects.create(
            short_code=code,
            description=cd.get("description") or "",
            password=cd.get("password1") or "",
            max_downloads=cd.get("max_downloads") or 0,
            expires_at=cd.get("expires_at"),
            owner=self.request.user if self.request.user.is_authenticated else None,
            ready=False,
        )
        files = (
            self.request.FILES.getlist("files")
            or self.request.FILES.getlist("files[]")
        )
        for f in files:
            FileItem.objects.create(archive=archive, file=f)

        res = build_zip.apply_async((archive.id,))
        archive.build_task_id = res.id
        archive.save(update_fields=["build_task_id"])

        return redirect("wait", code=archive.short_code)


class WaitView(TemplateView):
    template_name = "wait.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["archive"] = get_object_or_404(Archive, short_code=kwargs["code"])
        return ctx


class DownloadView(View):
    def get(self, request, code):
        arch = get_object_or_404(Archive, short_code=code)

        if arch.expires_at and arch.expires_at < timezone.now():
            raise Http404

        if arch.max_downloads and arch.download_count >= arch.max_downloads:
            return HttpResponseForbidden()

        if arch.password and request.GET.get("password", "") != arch.password:
            return HttpResponseForbidden()

        Archive.objects.filter(pk=arch.pk).update(download_count=F("download_count") + 1)
        ClickLog.objects.create(
            archive=arch,
            referer=request.META.get("HTTP_REFERER", ""),
            ip_address=request.META.get("REMOTE_ADDR", ""),
        )

        try:
            p = os.path.join(settings.MEDIA_ROOT, arch.zip_file.name)
            return FileResponse(open(p, "rb"), as_attachment=True, filename=os.path.basename(p))
        except FileNotFoundError:
            return HttpResponse(status=200)



class DashboardView(LoginRequiredMixin, ListView):
    model = Archive
    template_name = "dashboard.html"
    context_object_name = "archives"

    def get_queryset(self):
        return self.request.user.archives.all()


class ArchiveDetailView(LoginRequiredMixin, DetailView):
    model = Archive
    template_name = "detail.html"
    context_object_name = "archive"
    slug_field = "short_code"
    slug_url_kwarg = "code"

    def get_queryset(self):
        return self.request.user.archives.all()


class StatsPageView(DetailView):
    model = Archive
    template_name = "stats.html"
    slug_field = "short_code"
    slug_url_kwarg = "code"


@login_required
def wait_progress(request, code):
    arch = get_object_or_404(Archive, short_code=code, owner=request.user)

    if arch.ready and arch.zip_file:
        return JsonResponse(
            {"state": "SUCCESS", "pct": 100, "url": arch.get_download_url()}
        )

    if arch.error:
        return JsonResponse({"state": "FAILURE", "pct": 0, "message": arch.error})

    if not arch.build_task_id:
        return JsonResponse({"state": "PENDING", "pct": 0})

    res = AsyncResult(arch.build_task_id)

    if res.failed():
        info = res.info or {}
        message = (
            info.get("exc") if isinstance(info, dict) and "exc" in info else str(info)
        )
        return JsonResponse({"state": "FAILURE", "pct": 0, "message": message})

    meta = res.info or {}
    pct = meta.get("pct", 0)

    if res.state == "SUCCESS":

        if not arch.ready:
            arch.ready = True
            arch.save(update_fields=["ready"])
        return JsonResponse(
            {"state": "SUCCESS", "pct": 100, "url": arch.get_download_url()}
        )

    return JsonResponse({"state": res.state, "pct": pct})

