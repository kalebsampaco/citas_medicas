from django.db import models


class Clinic(models.Model):
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=30)

    def __str__(self):
        return self.name

class Room(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="rooms")
    name = models.CharField(max_length=100)
    capacity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.clinic.name} - {self.name}"
