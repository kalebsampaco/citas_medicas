from django.db import models


class Schedule(models.Model):
    doctor = models.ForeignKey("doctors.Doctor", on_delete=models.CASCADE, related_name="schedules")
    room = models.ForeignKey("clinics.Room", on_delete=models.CASCADE, related_name="schedules")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_minutes = models.IntegerField(default=30)

    class Meta:
        unique_together = ("doctor", "room", "date", "start_time", "end_time")
