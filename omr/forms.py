from django import forms
from django.core.exceptions import ValidationError
from .models import UploadedFile
import os

MAX_UPLOAD_MB = 20  # change if needed

VALID_EXTS = {
    'OMR': ['.pdf', '.zip'],
    'KEY': ['.csv'],
}

# omr/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import UploadedFile
import os

MAX_UPLOAD_MB = 20  # adjust
VALID_EXTS = {
    'OMR': ['.pdf', '.zip'],
    'KEY': ['.csv'],
}

class UploadedFileForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ['file', 'file_type']

    def clean(self):
        cleaned = super().clean()

        uploaded = cleaned.get('file')
        file_type = cleaned.get('file_type')

        # Basic presence checks
        if not uploaded:
            raise ValidationError({'file': "No file uploaded."})
        if not file_type:
            raise ValidationError({'file_type': "Please select a file type."})

        # Extension check
        ext = os.path.splitext(uploaded.name)[1].lower()
        allowed = VALID_EXTS.get(file_type, [])
        if ext not in allowed:
            raise ValidationError({
                'file': f"Invalid extension {ext} for {file_type}. Allowed: {', '.join(allowed)}"
            })

        # Size check
        if uploaded.size > MAX_UPLOAD_MB * 1024 * 1024:
            raise ValidationError({
                'file': f"File too large. Max {MAX_UPLOAD_MB} MB."
            })

        # Optionally: simple MIME/content_type hint (not foolproof)
        # content_type = uploaded.content_type
        # if file_type == 'OMR' and content_type not in ('application/pdf', 'application/zip'):
        #     pass

        return cleaned

