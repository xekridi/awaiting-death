from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from ..models.archive import Archive

class ArchiveDetailView(LoginRequiredMixin, DetailView):
    model               = Archive
    template_name       = "detail.html"
    context_object_name = "archive"
    slug_field          = "short_code"
    slug_url_kwarg      = "code"
    login_url           = reverse_lazy("login")

    def get_queryset(self):
        return self.request.user.archives.all()
