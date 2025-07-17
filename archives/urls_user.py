from django.urls import path
from .views_user import (
    HomePage, SignupView, UploadView, WaitView,
    DownloadView, DashboardView, ArchiveDetailView, StatsPageView, wait_progress
)

urlpatterns = [
    path("", HomePage.as_view(), name="home"),
    path("signup/", SignupView.as_view(), name="signup"),
    path("upload/", UploadView.as_view(), name="upload"),
    path("wait/<str:code>/", WaitView.as_view(), name="wait"),
    path("d/<str:code>/", DownloadView.as_view(), name="download"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("dashboard/<str:code>/", ArchiveDetailView.as_view(), name="archive-detail"),
    path("stats/<str:code>/", StatsPageView.as_view(), name="stats"),
    path("wait/<str:code>/progress/", wait_progress, name="wait-progress"),
]