from django import forms
from .models import Exam


class UploadForm(forms.ModelForm):
    answer_sheets = forms.FileField(
        required=False,
        help_text="Upload answer sheets (PDF only)",
    )
    answer_key = forms.FileField(
        required=False,
        help_text="Upload answer key (CSV or JSON)",
    )

    class Meta:
        model = Exam
        fields = ['exam_name', 'org_name', 'exam_date', 'sheet_template', 'subject', 'pass_mark']

    def clean_answer_sheets(self):
        file = self.cleaned_data.get("answer_sheets")
        if file and not file.name.lower().endswith(".pdf"):
            raise forms.ValidationError("Only PDF files are allowed for answer sheets.")
        return file

    def clean_answer_key(self):
        file = self.cleaned_data.get("answer_key")
        if file and not (file.name.lower().endswith(".csv") or file.name.lower().endswith(".json")):
            raise forms.ValidationError("Only CSV or JSON files are allowed for answer keys.")
        return file

