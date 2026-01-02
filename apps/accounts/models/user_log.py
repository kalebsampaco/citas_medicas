import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from .company import Company
from .user import User


class InvoiceUsageLog(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    invoice_id = models.UUIDField()
    action = models.CharField(max_length=50)  # 'created', 'sent_dgii', 'failed'
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'accounts'
        indexes = [
            models.Index(fields=['company', 'created_at']),
        ]
