from django.db import models


class Schedule(models.Model):
    doctor = models.ForeignKey("doctors.Doctor", on_delete=models.CASCADE, related_name="schedules")
    clinic = models.ForeignKey("clinics.Clinic", on_delete=models.CASCADE, related_name="schedules")
    # Room can be optional for disponibilidad general
    room = models.ForeignKey("clinics.Room", on_delete=models.SET_NULL, related_name="schedules", null=True, blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_minutes = models.IntegerField(default=30)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = ("doctor", "room", "date", "start_time", "end_time")
        verbose_name = 'Schedule'
        verbose_name_plural = 'Schedules'
        db_table = 'schedules'
        ordering = ['-id']
