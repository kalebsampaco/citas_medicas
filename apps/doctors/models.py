from apps.accounts.models.company import Company
from apps.accounts.models.user import User
from apps.clinics.models import Clinic, Room
from django.db import models


class Doctor(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=30)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='doctors', null=True, blank=True)
    clinic = models.ForeignKey(Clinic, on_delete=models.SET_NULL, related_name='doctors', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='doctors_created', null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, related_name='doctors', null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.specialty}"

    class Meta:
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctors'
        db_table = 'doctors'
        ordering = ['-id']
