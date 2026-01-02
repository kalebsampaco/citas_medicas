import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from .company import Company
from .role import Role


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Avatar del usuario (solo editable por COMPANY_ADMIN)
    avatar = models.FileField(upload_to='user_avatars/', blank=True, null=True)

    class Meta:
        app_label = 'accounts'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.company or 'No Company'})"

    @property
    def is_super_admin(self):
        return self.role and self.role.role_type == 'SUPER_ADMIN'

    @property
    def is_company_admin(self):
        return self.role and self.role.role_type == 'COMPANY_ADMIN'

    def has_permission(self, perm: str) -> bool:
        if self.is_super_admin:
            return True
        if not self.role:
            return False
        return self.role.permissions.get(perm, False)
