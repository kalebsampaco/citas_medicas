"""
Señales (Signals) para automatizar el envío de mensajes WhatsApp
cuando se crean o modifican citas.
"""

from datetime import datetime, timedelta

from apps.appointments.models import Appointment, AppointmentStatus
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Notification
from .services import send_whatsapp_message
from .templates import render_template


@receiver(post_save, sender=Appointment)
def send_appointment_created_notification(sender, instance: Appointment, created: bool, **kwargs):
    """
    Envía un mensaje WhatsApp cuando se crea una nueva cita.
    Solo se ejecuta cuando la cita es NUEVA (created=True).
    """
    if not created:
        return  # Solo en creación, no en actualizaciones

    try:
        # Preparar contexto para la plantilla
        context = {
            'patient_name': instance.patient.first_name,
            'appointment_date': instance.start_datetime.strftime('%d/%m/%Y'),
            'appointment_time': instance.start_datetime.strftime('%H:%M'),
            'doctor_name': instance.doctor.first_name,
            'clinic_name': instance.room.clinic.name,
        }

        # Renderizar mensaje
        message_body = render_template('appointment_created', context)

        # Enviar mensaje
        to_whatsapp = f"whatsapp:{instance.patient.phone_number}"
        message_sid = send_whatsapp_message(
            to_whatsapp=to_whatsapp,
            body=message_body,
            appointment=instance,
            notification=None
        )

        # Crear registro de notificación
        Notification.objects.create(
            appointment=instance,
            channel='whatsapp',
            to=to_whatsapp,
            template='appointment_created',
            status='sent',
            external_id=message_sid,
            delivered_at=timezone.now()
        )

        print(f"✅ Mensaje de cita creada enviado a {instance.patient.phone_number}")

    except Exception as e:
        print(f"❌ Error enviando notificación de cita creada: {str(e)}")
        # Registrar error pero no lanzar excepción para no afectar la creación de la cita


def send_appointment_reminder(appointment: Appointment, template_name: str):
    """
    Función auxiliar para enviar recordatorios de citas.

    Args:
        appointment: Instancia de Appointment
        template_name: Nombre de la plantilla ('appointment_reminder_48h' o 'appointment_reminder_24h')
    """
    try:
        # Preparar contexto para la plantilla
        context = {
            'patient_name': appointment.patient.first_name,
            'appointment_date': appointment.start_datetime.strftime('%d/%m/%Y'),
            'appointment_time': appointment.start_datetime.strftime('%H:%M'),
            'doctor_name': appointment.doctor.first_name,
            'clinic_name': appointment.room.clinic.name,
        }

        # Renderizar mensaje
        message_body = render_template(template_name, context)

        # Enviar mensaje
        to_whatsapp = f"whatsapp:{appointment.patient.phone_number}"
        message_sid = send_whatsapp_message(
            to_whatsapp=to_whatsapp,
            body=message_body,
            appointment=appointment,
            notification=None
        )

        # Crear registro de notificación
        Notification.objects.create(
            appointment=appointment,
            channel='whatsapp',
            to=to_whatsapp,
            template=template_name,
            status='sent',
            external_id=message_sid,
            delivered_at=timezone.now()
        )

        print(f"✅ Recordatorio enviado a {appointment.patient.phone_number}")

    except Exception as e:
        print(f"❌ Error enviando recordatorio: {str(e)}")
