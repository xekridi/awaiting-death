from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

urlpatterns = [
    path('health/', lambda r: HttpResponse('OK'), name='health'),
    path('admin/',  admin.site.urls),
    path("", include("archives.urls")),
    path("api/", include("api.routers.router.urls")),
    path('accounts/', include('accounts.urls')),
]
