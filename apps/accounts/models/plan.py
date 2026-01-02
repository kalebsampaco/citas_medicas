import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Plan(models.Model):
    PLAN_TYPES = [
        ('FREE', 'Free'),
        ('BASIC', 'Basic'),
        ('PRO', 'Pro'),
        ('ENTERPRISE', 'Enterprise'),
    ]
    name = models.CharField(max_length=50, unique=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    max_invoices = models.IntegerField(default=10)
    max_users = models.IntegerField(default=1)
    max_roles = models.IntegerField(default=2)
    max_clinics = models.IntegerField(default=1, help_text="Máximo de clínicas permitidas")
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    features = models.JSONField(default=dict)  # {"reports": true, "api_access": false}
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'accounts'

    def __str__(self):
        return f"{self.name} ({self.plan_type})"
