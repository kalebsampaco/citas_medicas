import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .plan import Plan


class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    rnc = models.CharField(max_length=20, unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    # DGII Config
    dgii_certificate_uploaded = models.BooleanField(default=False)
    dgii_ambiente_default = models.CharField(max_length=20, default='testecf')
    # Plan
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    invoice_count = models.IntegerField(default=0)
    invoice_limit = models.IntegerField(default=0)  # Copiado del plan al crear
    user_limit = models.IntegerField(default=0)
    role_limit = models.IntegerField(default=0)
    clinic_limit = models.IntegerField(default=0)  # Copiado del plan al crear
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Logo de la empresa (se almacena la ruta/clave en S3)
    logo = models.FileField(upload_to='company_logos/', blank=True, null=True)

    class Meta:
        app_label = 'accounts'

    def __str__(self):
        return f"{self.name} ({self.rnc})"

    @property
    def invoices_remaining(self):
        return max(self.invoice_limit - self.invoice_count, 0)

    @property
    def is_over_limit(self):
        return self.invoice_count >= self.invoice_limit and self.invoice_limit > 0

    @property
    def is_near_limit(self):
        if self.is_over_limit:
            return False
        if self.invoice_limit <= 0:
            return False
        return self.invoice_count >= (self.invoice_limit - 2)

    @property
    def clinics_count(self):
        from apps.clinics.models import Clinic
        return Clinic.objects.filter(company=self).count()

    @property
    def clinics_remaining(self):
        return max(self.clinic_limit - self.clinics_count, 0)

    @property
    def is_clinics_over_limit(self):
        return self.clinics_count >= self.clinic_limit and self.clinic_limit > 0

    @property
    def is_payment_active(self):
        from .plan_payment import PlanPayment
        today = timezone.now().date()
        month_start = today.replace(day=1)
        return PlanPayment.objects.filter(company=self, paid_month=month_start).exists()
