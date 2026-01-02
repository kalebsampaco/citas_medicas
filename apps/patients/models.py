from apps.accounts.models.company import Company
from apps.accounts.models.user import User
from django.db import models


class Patient(models.Model):
    DOCUMENT_CHOICES = [
        ("CEDULA", "Cédula"),
        ("PASAPORTE", "Pasaporte"),
        ("RNC", "RNC"),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_CHOICES, default="CEDULA")
    document_number = models.CharField(max_length=50, unique=True)
    birth_date = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=30)
    email = models.EmailField(null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='patients', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='patients_created', null=True, blank=True)
    insurance_provider = models.CharField(max_length=120, null=True, blank=True)
    insurance_number = models.CharField(max_length=80, null=True, blank=True)
    emergency_contact = models.CharField(max_length=100, null=True, blank=True)
    emergency_phone = models.CharField(max_length=30, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.document_number}"

    class Meta:
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
        db_table = 'patients'
        ordering = ['-id']
