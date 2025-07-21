from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from api.routers import router

urlpatterns = [
    path('health/', lambda r: HttpResponse('OK'), name='health'),
    path('admin/',  admin.site.urls),
    path("", include("archives.urls")),
    path("api/", include(router.urls)),
    path('accounts/', include("accounts.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
