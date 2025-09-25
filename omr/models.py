from django.db import models

class UploadedFile(models.Model):
    FILE_TYPES = [
        ('sheet', 'OMR Sheet'),
        ('answer_key', 'Answer Key'),
    ]

    file = models.FileField(upload_to='uploads/')
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_file_type_display()} — {self.file.name}"

