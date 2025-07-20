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

    def validate(self, data):
        if self.required and not data:
            raise forms.ValidationError(self.error_messages['required'], code='required')
        for f in data:
            super(forms.FileField, self).validate(f)

class UploadForm(forms.Form):
    files         = MultiFileField(
                        required=True,
                        widget=MultiFileInput(attrs={"multiple": True}),
                        label="Выберите файлы"
                     )
    description   = forms.CharField(required=False)
    password1     = forms.CharField(required=False)
    password2     = forms.CharField(required=False)
    max_downloads = forms.IntegerField(min_value=0, required=False)
    expires_at    = forms.DateTimeField(required=False)

    def clean(self):
        cleaned = super().clean()
        files = cleaned.get("files")
        if not files:
            raise forms.ValidationError("Нужно выбрать хотя бы один файл.")
        return cleaned
