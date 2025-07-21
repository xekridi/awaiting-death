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


class DownloadView(View):
    template_name = "download.html"

    def get(self, request, code):
        archive = self._get_archive_or_404(code)

        if archive.password and not request.session.get(self._session_key(archive)):
            return render(request, self.template_name, {"archive": archive})

        return self._serve_file(request, archive)

    def post(self, request, code):
        archive = self._get_archive_or_404(code)

        if archive.password:
            pwd = request.POST.get("password", "")
            if not archive.check_password(pwd):
                return render(request, self.template_name, {"archive": archive, "error": "Неверный пароль"})
            request.session[self._session_key(archive)] = True

        return self._serve_file(request, archive)

    def _get_archive_or_404(self, code):
        archive = get_object_or_404(Archive, short_code=code, ready=True)
        if archive.expires_at and archive.expires_at < timezone.now():
            raise Http404
        if archive.max_downloads and archive.download_count >= archive.max_downloads:
            raise HttpResponseForbidden
        return archive

    def _session_key(self, archive):
        return f"download_access_{archive.pk}"

    def _serve_file(self, request, archive):
        filepath = archive.zip_file.path
        filename = f"{archive.name}.zip"
        response = FileResponse(open(filepath, "rb"), as_attachment=True, filename=filename)
        archive.download_count += 1
        archive.save(update_fields=["download_count"])
        return response





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
