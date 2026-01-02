"""
Command: Enviar recordatorios automáticos de citas
Uso: python manage.py send_appointment_reminders
"""

from datetime import timedelta

from apps.appointments.models import Appointment, AppointmentStatus
from apps.notifications.models import Notification
from apps.notifications.signals import send_appointment_reminder
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Envía recordatorios automáticos de citas (48h y 24h antes)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar sin enviar mensajes reales',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()

        # Recordatorio 48 horas antes
        self.send_reminders_48h(now, dry_run)

        # Recordatorio 24 horas antes
        self.send_reminders_24h(now, dry_run)

    def send_reminders_48h(self, now, dry_run):
        """Envía recordatorios 48 horas antes de la cita."""
        # Calcular rango: entre 47h y 49h antes
        min_time = now + timedelta(hours=47)
        max_time = now + timedelta(hours=49)

        appointments = Appointment.objects.filter(
            start_datetime__gte=min_time,
            start_datetime__lte=max_time,
            status=AppointmentStatus.PENDING,  # Solo citas pendientes
        ).exclude(
            # No enviar si ya se envió un recordatorio de 48h
            notifications__template='appointment_reminder_48h'
        )

        for appointment in appointments:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"[DRY-RUN] Recordatorio 48h para {appointment.patient.first_name} "
                        f"({appointment.patient.phone_number}) - {appointment.start_datetime}"
                    )
                )
            else:
                try:
                    send_appointment_reminder(appointment, 'appointment_reminder_48h')
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Recordatorio 48h enviado a {appointment.patient.phone_number}"
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ Error enviando recordatorio 48h: {str(e)}"
                        )
                    )

    def send_reminders_24h(self, now, dry_run):
        """Envía recordatorios 24 horas antes de la cita."""
        # Calcular rango: entre 23h y 25h antes
        min_time = now + timedelta(hours=23)
        max_time = now + timedelta(hours=25)

        appointments = Appointment.objects.filter(
            start_datetime__gte=min_time,
            start_datetime__lte=max_time,
            status=AppointmentStatus.PENDING,
        ).exclude(
            notifications__template='appointment_reminder_24h'
        )

        for appointment in appointments:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"[DRY-RUN] Recordatorio 24h para {appointment.patient.first_name} "
                        f"({appointment.patient.phone_number}) - {appointment.start_datetime}"
                    )
                )
            else:
                try:
                    send_appointment_reminder(appointment, 'appointment_reminder_24h')
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Recordatorio 24h enviado a {appointment.patient.phone_number}"
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ Error enviando recordatorio 24h: {str(e)}"
                        )
                    )
