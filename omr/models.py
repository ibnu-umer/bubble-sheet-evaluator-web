from django.db import models


class UploadLog(models.Model):
    filename = models.CharField(max_length=255)
    filetype = models.CharField(max_length=20)  # "sheet" or "key"
    uploaded_at = models.DateTimeField(auto_now_add=True)

