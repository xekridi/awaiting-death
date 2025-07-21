from django.urls import path
from .views_user import (
    HomePage,
    UploadView,
    WaitView,
    wait_progress,
    DashboardView,
    ArchiveDetailView,
    DownloadView,
    StatsPageView,
    PreviewView,
)
from accounts.views import SignUpView

urlpatterns = [
    path("",                         HomePage.as_view(),     name="home"),
    path("upload/",                  UploadView.as_view(),   name="upload"),

    path("wait/<str:code>/",         WaitView.as_view(),     name="wait"),
    path("wait/<str:code>/progress/",wait_progress,          name="wait-progress"),

    path("d/<str:code>/preview/",    PreviewView.as_view(),  name="download-page"),
    path("d/<str:code>/",            DownloadView.as_view(), name="download"),
    path("d/<str:code>/file/",       DownloadView.as_view(), name="download-file"),

    path("dashboard/",               DashboardView.as_view(),     name="dashboard"),
    path("dashboard/<str:code>/",    ArchiveDetailView.as_view(), name="archive-detail"),
    path("stats/<str:code>/",        StatsPageView.as_view(),     name="stats"),
]