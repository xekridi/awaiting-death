from django import forms
from .models import Archive

class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class ArchiveCreateForm(forms.ModelForm):
    password      = forms.CharField(
        required=False, widget=forms.PasswordInput, label="Пароль"
    )
    expires_at    = forms.DateTimeField(
        required=False, label="Истекает в"
    )
    max_downloads = forms.IntegerField(
        required=False, min_value=1, label="Максимум загрузок"
    )

    class Meta:
        model = Archive
        fields = ("description", "password", "expires_at", "max_downloads")

class UploadForm(forms.Form):
    description   = forms.CharField(required=False, label="Описание")
    files         = forms.FileField(
        widget=MultiFileInput(attrs={"multiple": True}),
        required=True,
        label="Файлы",
    )
    password1     = forms.CharField(
        required=False, widget=forms.PasswordInput, label="Пароль"
    )
    password2     = forms.CharField(
        required=False, widget=forms.PasswordInput, label="Повтор пароля"
    )
    max_downloads = forms.IntegerField(
        required=False, min_value=1, label="Максимум загрузок"
    )
    expires_at    = forms.DateTimeField(required=False, label="Истекает в")

    def clean(self):
        cd = super().clean() or {}
        if cd.get("password1") != cd.get("password2"):
            self.add_error("password2", "Пароли не совпадают")
        return cd