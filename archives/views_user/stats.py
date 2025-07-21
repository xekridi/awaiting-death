from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models.archive import Archive
from ..services.stats import get_downloads_by_day, get_top_referers


class StatsPageView(LoginRequiredMixin, TemplateView):
    template_name = "stats.html"
    login_url    = "login"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        short_code = kwargs.get("short_code")
        ctx["archive"]      = Archive.objects.get(short_code=short_code)
        ctx["by_day"]       = get_downloads_by_day(short_code)
        ctx["top_referers"] = get_top_referers(short_code)
        return ctx

class StatsAPIView(APIView):
    def get(self, request, short_code):
        return Response({
            "by_day": get_downloads_by_day(short_code),
            "top_referers": get_top_referers(short_code),
        })
