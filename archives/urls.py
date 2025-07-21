from django.urls import path
from .views_user.home import HomePage
from .views_user.upload import UploadView, WaitView, wait_progress
from .views_user.download import DownloadPageView, DownloadView
from .views_user.dashboard import DashboardView
from .views_user.detail import ArchiveDetailView
from .views_user.stats import StatsPageView, StatsAPIView
from .views_user.preview  import PreviewView

urlpatterns = [
    path("",                          HomePage.as_view(),          name="home"),
    path("upload/",                   UploadView.as_view(),        name="upload"),
    path("wait/<str:code>/",          WaitView.as_view(),          name="wait"),
    path("wait/<str:code>/progress/", wait_progress,               name="wait-progress"),
    path("d/<str:code>/preview/",     PreviewView.as_view(),       name="preview"),
    path("d/<str:code>/",             DownloadPageView.as_view(),  name="download-page"),
    path("d/<str:code>/file/",        DownloadView.as_view(),      name="download"),
    path("dashboard/",                DashboardView.as_view(),     name="dashboard"),
    path("d/<str:code>/detail/",      ArchiveDetailView.as_view(), name="detail"),
    path("stats/<str:code>/",         StatsPageView.as_view(),     name="stats"),
    path("api/stats/<str:code>/",     StatsAPIView.as_view(),      name="stats-api"),
]
