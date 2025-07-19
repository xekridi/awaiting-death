# archives/views.py

import os
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.http import FileResponse, HttpResponseForbidden, Http404
from django.db.models import F
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView

from rest_framework.views import APIView
from rest_framework.response import Response

from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Archive, ClickLog
from .business.stats import get_downloads_by_day, get_top_referers


class DashboardView(LoginRequiredMixin, ListView):
    model = Archive
    template_name = "dashboard.html"
    context_object_name = "archives"
    login_url = "login"

    def get_queryset(self):
        return Archive.objects.filter(owner=self.request.user, deleted_at__isnull=True)


class DownloadView(View):
    template_name = "download.html"

    def get(self, request, code):
        archive = get_object_or_404(Archive, short_code=code, ready=True)
        if archive.expires_at and archive.expires_at < timezone.now():
            raise Http404
        if archive.max_downloads and archive.download_count >= archive.max_downloads:
            return HttpResponseForbidden
        if archive.password:
            pwd = request.GET.get("password")
            if not pwd:
                return render(request, self.template_name, {"archive": archive})
            if pwd != archive.password:
                return HttpResponseForbidden
        Archive.objects.filter(pk=archive.pk).update(
            download_count=F("download_count") + 1
        )
        ClickLog.objects.create(
            archive=archive,
            referer=request.META.get("HTTP_REFERER", ""),
            ip_address=request.META.get("REMOTE_ADDR", ""),
        )
        file_path = archive.zip_file.path
        if not os.path.exists(file_path):
            raise Http404
        return FileResponse(
            open(file_path, "rb"),
            as_attachment=True,
            filename=os.path.basename(file_path),
        )


class StatsAPIView(APIView):
    def get(self, request, short_code):
        return Response({
            "by_day": get_downloads_by_day(short_code),
            "top_referers": get_top_referers(short_code),
        })


class StatsPageView(TemplateView):
    template_name = "stats.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        code = self.kwargs.get("short_code")
        context.update({
            "short_code": code,
            "by_day": get_downloads_by_day(code),
            "top_referers": get_top_referers(code),
        })
        return context
