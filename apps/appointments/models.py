from django.db import models


class AppointmentStatus(models.TextChoices):
    PENDING = "PENDING", "Pendiente"
    CONFIRMED = "CONFIRMED", "Confirmada"
    RESCHEDULED = "RESCHEDULED", "Reprogramada"
    CANCELLED = "CANCELLED", "Cancelada"
    COMPLETED = "COMPLETED", "Completada"
    NO_SHOW = "NO_SHOW", "No asistió"

class Appointment(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="appointments")
    schedule = models.ForeignKey("schedules.Schedule", on_delete=models.PROTECT, related_name="appointments")
    doctor = models.ForeignKey("doctors.Doctor", on_delete=models.PROTECT)
    room = models.ForeignKey("clinics.Room", on_delete=models.PROTECT)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    status = models.CharField(max_length=20, choices=AppointmentStatus.choices, default=AppointmentStatus.PENDING)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
        db_table = 'appointments'
        ordering = ['-id']

class AppointmentAction(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="actions")
    action = models.CharField(max_length=30)  # confirm/reschedule/cancel
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'AppointmentAction'
        verbose_name_plural = 'AppointmentActions'
        db_table = 'appointmentActions'
        ordering = ['-id']
