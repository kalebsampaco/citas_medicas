from django.db import models


class Notification(models.Model):
    appointment = models.ForeignKey("appointments.Appointment", on_delete=models.CASCADE, related_name="notifications")
    channel = models.CharField(max_length=20, default="whatsapp")
    to = models.CharField(max_length=50)
    template = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default="queued")
    external_id = models.CharField(max_length=100, null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.channel} -> {self.to} ({self.status})"
