from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = "ADMIN", "Administrador"
    OPERATOR = "OPERATOR", "Operador de Citas"

class User(AbstractUser):
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.OPERATOR)

    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    @property
    def is_operator(self):
        return self.role == Role.OPERATOR

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        db_table = 'users'
        ordering = ['-date_joined']
