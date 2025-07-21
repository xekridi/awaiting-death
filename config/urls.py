from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from archives.views_user import (
    HomePage, UploadView, WaitView, wait_progress,
    DashboardView, ArchiveDetailView, StatsPageView, PreviewView,
)

urlpatterns = [
    path('health/', lambda r: HttpResponse('OK'), name='health'),
    path('admin/',  admin.site.urls),
    path("", include("archives.urls_user")),
    path("api/", include("archives.api.urls")),
    path('accounts/', include('accounts.urls')),
]