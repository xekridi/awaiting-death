from django.urls import path

from .views_user import (
    ArchiveDetailView,
    DashboardView,
    DownloadPageView,
    HomePage,
    PreviewView,
    StatsPageView,
    UploadView,
    WaitView,
    wait_progress,
)

urlpatterns = [
    path("",        HomePage.as_view(),     name="home"),
    path("upload/", UploadView.as_view(),   name="upload"),

    path("wait/<str:code>/",          WaitView.as_view(),     name="wait"),
    path("wait/<str:code>/progress/", wait_progress,          name="wait-progress"),

    path("d/<str:code>/preview/", PreviewView.as_view(),  name="download-page"),
    path("d/<str:code>/",         DownloadPageView.as_view(), name="download"),
    path("d/<str:code>/file/",    DownloadPageView.as_view(), name="download-file"),

    path("dashboard/",            DashboardView.as_view(),     name="dashboard"),
    path("dashboard/<str:code>/", ArchiveDetailView.as_view(), name="archive-detail"),
    path("stats/<str:code>/",     StatsPageView.as_view(),     name="stats"),
]
