import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from .company import Company


class Role(models.Model):
    ROLE_TYPES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('COMPANY_ADMIN', 'Company Admin'),
        ('ACCOUNTANT', 'Accountant'),
        ('VIEWER', 'Viewer'),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='roles', null=True, blank=True)
    name = models.CharField(max_length=100)
    role_type = models.CharField(max_length=30, choices=ROLE_TYPES)
    permissions = models.JSONField(default=dict)  # {"citas.create": true, "citas.view": true, "reports.view": true, ...}
    is_system = models.BooleanField(default=False)  # Super Admin roles
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'accounts'
        unique_together = ['company', 'name']

    def __str__(self):
        return f"{self.name} ({self.company or 'System'})"
