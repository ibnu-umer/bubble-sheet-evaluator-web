from django.db import models

class UploadedFile(models.Model):
    FILE_TYPES = [
        ('OMR', 'OMR Sheet'),
        ('KEY', 'Answer Key'),
    ]

    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_type} — {self.file.name}"
