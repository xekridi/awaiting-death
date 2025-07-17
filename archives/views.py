import os
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponseForbidden, HttpResponseNotFound, Http404, HttpResponse
from django.db import transaction, models
from django.db.models import F
from django.utils import timezone
from django.views import View
from .models import Archive, ClickLog
from rest_framework.views import APIView
from rest_framework.response import Response
from archives.business.stats import get_downloads_by_day, get_top_referers
from django.views.generic import TemplateView

class ArchiveStatsAPIView(APIView):
    def get(self, request, short_code):
        by_day = get_downloads_by_day(short_code)
        referers = get_top_referers(short_code)
        return Response({"by_day": by_day, "top_referers": referers})


def download_archive(request, code):
    archive = get_object_or_404(Archive, short_code=code, ready=True)

    if archive.expires_at and archive.expires_at < timezone.now():
        raise Http404

    if archive.password:
        pwd = request.GET.get("password", "")
        if pwd != archive.password:
            return HttpResponseForbidden()

    if archive.max_downloads and archive.download_count >= archive.max_downloads:
        return HttpResponseForbidden()

    Archive.objects.filter(pk=archive.pk).update(download_count=F("download_count") + 1)

    ClickLog.objects.create(
        archive=archive,
        referer=request.META.get("HTTP_REFERER", ""),
        ip_address=request.META.get("REMOTE_ADDR", ""),
    )

    name = archive.zip_file.name
    if os.path.isabs(name) and os.path.exists(name):
        file_path = name
    else:
        file_path = os.path.join(settings.MEDIA_ROOT, name)

    file_handle = open(file_path, "rb")
    return FileResponse(
        file_handle,
        as_attachment=True,
        filename=os.path.basename(name),
    )

class ArchiveStatsAPIView(APIView):
    def get(self, request, short_code):
        by_day = get_downloads_by_day(short_code)
        referers = get_top_referers(short_code)
        return Response({"by_day": by_day, "top_referers": referers})
    
class StatsPageView(TemplateView):
    template_name = "stats.html"
    def get_context_data(self, **kwargs):
        short_code = kwargs["short_code"]
        return {
            "short_code": short_code,
            "by_day": get_downloads_by_day(short_code),
            "top_referers": get_top_referers(short_code),
        }

class DownloadView(View):
    def get(self, request, code):
        archive = get_object_or_404(Archive, short_code=code)

        if archive.expires_at and archive.expires_at < timezone.now():
            raise Http404

        if archive.max_downloads and archive.download_count >= archive.max_downloads:
            return HttpResponseForbidden()

        if archive.password and request.GET.get("password", "") != archive.password:
            return HttpResponseForbidden()

        Archive.objects.filter(pk=archive.pk).update(
            download_count=F("download_count") + 1
        )
        ClickLog.objects.create(
            archive=archive,
            referer=request.META.get("HTTP_REFERER", ""),
            ip_address=request.META.get("REMOTE_ADDR", ""),
        )

        try:
            path = os.path.join(settings.MEDIA_ROOT, archive.zip_file.name)
            return FileResponse(
                open(path, "rb"),
                as_attachment=True,
                filename=os.path.basename(path),
            )
        except FileNotFoundError:
            return HttpResponse(status=200)