from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from archives.views_user import (
    HomePage, UploadView, WaitView, wait_progress,
    DashboardView, DownloadView, StatsPageView,
)

def health(request):
    return HttpResponse("OK")

urlpatterns = [
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),

    path("", include("accounts.urls")),

    path("", HomePage.as_view(), name="home"),
    path("upload/", UploadView.as_view(), name="upload"),
    path("wait/<str:code>/", WaitView.as_view(), name="wait"),
    path("wait/<str:code>/progress/", wait_progress, name="wait-progress"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("d/<str:code>/", DownloadView.as_view(), name="download"),
    path("stats/<str:short_code>/", StatsPageView.as_view(), name="stats"),

    path("api/", include("archives.api.urls")),
]
