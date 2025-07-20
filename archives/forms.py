from django import forms
from django.forms.widgets import FileInput


class MultiFileInput(FileInput):
    allow_multiple_selected = True


class UploadForm(forms.Form):
    description   = forms.CharField(
        max_length=255, required=False, label="Описание"
    )

    files         = forms.FileField(
        widget=MultiFileInput(attrs={"multiple": True}),
        required=True,
        label="Файлы (можно несколько)",
    )

    password1     = forms.CharField(
        widget=forms.PasswordInput, required=False, label="Пароль"
    )
    password2     = forms.CharField(
        widget=forms.PasswordInput, required=False, label="Повтор пароля"
    )
    max_downloads = forms.IntegerField(
        min_value=0, required=False, label="Макс. скачиваний"
    )
    expires_at    = forms.DateTimeField(
        required=False, label="Срок действия (UTC)"
    )

    def clean(self):
        cleaned = super().clean()

        if not self.files.getlist("files"):
            self.add_error("files", "Нужно выбрать хотя бы один файл")

        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 or p2:
            if p1 != p2:
                self.add_error("password2", "Пароли не совпадают")

        return cleaned
