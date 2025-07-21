from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from ..models.archive import Archive


class PreviewView(View):
    def get(self, request, code):
        archive = get_object_or_404(Archive, short_code=code, deleted_at__isnull=True)
        if not archive.ready:
            return redirect("wait", code=code)
        files = archive.files.all()
        return render(request, "archives/preview.html", {
            "archive": archive,
            "files": files,
        })
