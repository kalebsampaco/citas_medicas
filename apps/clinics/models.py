from django.db import models


class Clinic(models.Model):
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=30)
    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="clinics", null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Clinic'
        verbose_name_plural = 'Clinics'
        db_table = 'clinics'
        ordering = ['-id']

class Room(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="rooms")
    name = models.CharField(max_length=100)
    capacity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.clinic.name} - {self.name}"

    class Meta:
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'
        db_table = 'rooms'
        ordering = ['-id']
