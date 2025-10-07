from django.db import models
from django.conf import settings
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

    # owner / who created the exam
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exams",
        null=True,        # if you have old exams, set nullable and migrate, then backfill
        blank=True
    )

    def __str__(self):
        return f"{self.exam_name} ({self.subject})"



class Result(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="results")
    roll_no = models.CharField(max_length=20)
    answers = models.JSONField(blank=True, null=True)  # optional: store {"Q1": "A", "Q2": "B"}
    score = models.FloatField()
    sheet = models.ImageField(upload_to='evaluated/', null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("exam", "roll_no")  # one result per student per exam

    def __str__(self):
        return f"{self.roll_no} - {self.exam.exam_name} ({self.score})"
