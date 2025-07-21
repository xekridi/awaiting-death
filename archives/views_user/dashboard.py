from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from ..models.archive import Archive

class DashboardView(LoginRequiredMixin, ListView):
    model               = Archive
    template_name       = "dashboard.html"
    context_object_name = "archives"
    login_url           = reverse_lazy("login")

    def get_queryset(self):
        return self.request.user.archives.filter(deleted_at__isnull=True)
