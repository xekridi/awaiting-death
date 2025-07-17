from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from archives.views import download_archive
from archives.views_user import SignupView, CustomLogoutView


def health(request):
    return HttpResponse("OK")

urlpatterns = [
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
    path("signup/", SignupView.as_view(), name="signup"),
    path("api/", include("archives.api.urls")),
    path("d/<str:code>/", download_archive, name="download"),
    path("accounts/logout/", CustomLogoutView.as_view(), name="logout"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("archives.urls_user")),
]