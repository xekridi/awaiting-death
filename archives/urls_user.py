from django.urls import path
from .views_user import (
    HomePage,
    UploadView,
    WaitView,
    wait_progress,
    DashboardView,
    ArchiveDetailView,
)

urlpatterns = [
    path("", HomePage.as_view(), name="home"),
    path("upload/", UploadView.as_view(), name="upload"),
    path("wait/<str:code>/", WaitView.as_view(), name="wait"),
    path("wait/<str:code>/progress/", wait_progress, name="wait-progress"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("archive/<str:code>/", ArchiveDetailView.as_view(), name="archive-detail"),
]