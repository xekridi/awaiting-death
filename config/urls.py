from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

urlpatterns = [
    path('health/', lambda r: HttpResponse('OK'), name='health'),
    path('admin/',  admin.site.urls),
    path("", include("archives.urls_user")),
    path("api/", include("archives.api.urls")),
    path('accounts/', include('accounts.urls')),
]
