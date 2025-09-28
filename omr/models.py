from django.db import models
import uuid


class UploadLog(models.Model):
    filename = models.CharField(max_length=255)
    filetype = models.CharField(max_length=20)  # "sheet" or "key"
    uploaded_at = models.DateTimeField(auto_now_add=True)



class Exam(models.Model):
    TEMPLATE_CHOICES = [
        ('AS-01', 'AS-01'),
        ('AS-02', 'AS-02'),
        ('AS-03', 'AS-03'),
        ('AS-04', 'AS-04'),
    ]

    exam_name = models.CharField(max_length=255)
    org_name = models.CharField(max_length=255)
    exam_date = models.DateField()
    sheet_template = models.CharField(
        max_length=10,
        choices=TEMPLATE_CHOICES,
        default='AS-01'
    )
    subject = models.CharField(max_length=255, blank=True, null=True)
    pass_mark = models.IntegerField(blank=True, null=True)
    exam_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
