from django import forms
from django.forms.widgets import ClearableFileInput

class MultiFileInput(ClearableFileInput):
    allow_multiple_selected = True

class MultiFileField(forms.FileField):
    widget = MultiFileInput

    def to_python(self, data):
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            return list(data)
        return [data]

class UploadForm(forms.Form):
    name          = forms.CharField(label="Имя архива")
    description   = forms.CharField(required=False, label="Описание")
    files         = MultiFileField(label="Файлы", required=True)
    password1     = forms.CharField(label="Пароль (необязательно)", required=False, widget=forms.PasswordInput)
    password2     = forms.CharField(label="Повтор пароля", required=False, widget=forms.PasswordInput)
    max_downloads = forms.IntegerField(label="Максимум скачиваний", required=False, min_value=0)
    expires_at    = forms.DateTimeField(label="Срок жизни", required=False)

    def clean(self):
        cd = super().clean()
        if not cd.get("name"):
            raise forms.ValidationError("Имя архива обязательно")
        if cd.get("password1") != cd.get("password2"):
            self.add_error("password2", "Пароли не совпадают")
        if not cd.get("files"):
            raise forms.ValidationError("Нужно выбрать хотя бы один файл.")
        return cd
