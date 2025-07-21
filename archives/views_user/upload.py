import logging
from django.shortcuts import redirect
from django.views.generic import FormView, TemplateView
from django.http import JsonResponse, Http404
from django.contrib.auth.views import redirect_to_login
from celery.result import AsyncResult

from ..forms import UploadForm
from ..models.archive import Archive
from ..services.upload import handle_upload

logger = logging.getLogger("archives.views_user.upload")
logger.setLevel(logging.DEBUG)

class UploadView(FormView):
    template_name = "upload.html"
    form_class    = UploadForm

    def form_valid(self, form):
        archive = handle_upload(form.cleaned_data, self.request.user, self.request)
        return redirect("wait", code=archive.short_code)

    def form_invalid(self, form):
        logger.debug("UPLOAD errors: %s", form.errors.as_json())
        return super().form_invalid(form)

class WaitView(TemplateView):
    template_name = "wait.html"

    def get_context_data(self, **kwargs):
        archive = Archive.objects.get(short_code=kwargs["code"], deleted_at__isnull=True)
        return {"archive": archive}

def wait_progress(request, code):
    qs = Archive.objects.filter(short_code=code, deleted_at__isnull=True)
    if not request.user.is_authenticated:
        try:
            archive = qs.get(owner__isnull=True)
        except Archive.DoesNotExist:
            return redirect_to_login(request.get_full_path())
    else:
        archive = qs.get()
        if archive.owner and archive.owner != request.user:
            raise Http404()

    if archive.error:
        return JsonResponse({"state": "FAILURE", "message": archive.error, "pct": 0})
    if archive.ready:
        return JsonResponse({"state": "SUCCESS", "url": archive.get_download_url(), "pct": 100})
    if not archive.build_task_id:
        return JsonResponse({"state": "PENDING", "pct": 0})
    result = AsyncResult(archive.build_task_id)
    info   = getattr(result, "info", {}) or {}
    return JsonResponse({"state": result.state, "pct": info.get("pct", 0)})
