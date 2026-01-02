from apps.appointments.models import (Appointment, AppointmentAction,
                                      AppointmentStatus)
from apps.audit.services import log_model_change, log_twilio_inbound
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, views
from rest_framework.response import Response

from .models import Notification
from .services import send_whatsapp_message
from .templates import parse_user_response, render_template


class SendReminderView(views.APIView):
    def post(self, request, appointment_id: int):
        appointment = Appointment.objects.get(id=appointment_id)
        to = f"whatsapp:{appointment.patient.phone_number}"
        body = (
            f"Hola {appointment.patient.first_name}, tu cita con {appointment.doctor.first_name} "
            f"es el {appointment.start_datetime.strftime('%Y/%m/%d a las %H:%M')}. "
            "Responde: Confirmar / Reprogramar / Cancelar"
        )
        # Enviar mensaje (ahora con logging integrado)
        sid = send_whatsapp_message(
            to,
            body,
            notification=None,  # Se creará después
            appointment=appointment
        )

        # Crear notificación
        notification = Notification.objects.create(
            appointment=appointment,
            to=to,
            template="reminder_freeform",
            status="queued",
            external_id=sid,
        )

        # Registrar en auditoría
        log_model_change(
            instance=notification,
            action='CREATE',
            user=request.user if request.user.is_authenticated else None,
            ip_address=getattr(request, 'audit_ip', None),
            user_agent=getattr(request, 'audit_user_agent', None),
        )

        return Response({"message_sid": sid})


@method_decorator(csrf_exempt, name="dispatch")
class WhatsAppWebhookView(views.APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        from_number = request.data.get("From")  # whatsapp:+123...
        body = (request.data.get("Body") or "").strip()
        message_sid = request.data.get("MessageSid", "")

        # Find patient by phone (strip prefix)
        e164 = from_number.replace("whatsapp:", "") if from_number else None
        appointment = (
            Appointment.objects.filter(patient__phone_number=e164).order_by("-start_datetime").first()
        )
        if not appointment:
            return Response({"detail": "No appointment found"}, status=status.HTTP_404_NOT_FOUND)

        # Registrar mensaje entrante de Twilio
        log_twilio_inbound(
            message_sid=message_sid,
            from_number=from_number,
            to_number=request.data.get("To", ""),
            body=body,
            appointment=appointment,
            response_data=dict(request.data)
        )

        # Guardar estado anterior para auditoría
        old_status = appointment.status

        # Analizar respuesta del usuario usando plantilla mejorada
        action = parse_user_response(body, 'appointment_reminder_48h')

        if action:
            # Actualizar estado de la cita basado en la acción
            if action == "confirm":
                appointment.status = AppointmentStatus.CONFIRMED
            elif action == "reschedule":
                appointment.status = AppointmentStatus.RESCHEDULED
            elif action == "cancel":
                appointment.status = AppointmentStatus.CANCELLED

            appointment.save()

            # Registrar cambio de estado en auditoría
            log_model_change(
                instance=appointment,
                action='UPDATE',
                user=None,  # Cambio automático por webhook
                changes={
                    'status': {
                        'old': old_status,
                        'new': appointment.status
                    },
                    'trigger': 'whatsapp_webhook',
                    'message_sid': message_sid,
                    'user_action': action
                },
                ip_address=getattr(request, 'audit_ip', None),
                user_agent=getattr(request, 'audit_user_agent', None),
            )

            # Registrar acción en historial de cita
            AppointmentAction.objects.create(
                appointment=appointment,
                action=action,
                payload={"from": from_number, "body": body, "status_before": old_status}
            )

            # Generar respuesta personalizada según acción
            if action == "confirm":
                reply = (
                    f"¡Perfecto {appointment.patient.first_name}! Tu cita está confirmada para "
                    f"{appointment.start_datetime.strftime('%d/%m/%Y a las %H:%M')}. "
                    f"¡Te esperamos!"
                )
            elif action == "reschedule":
                reply = (
                    f"Entendido {appointment.patient.first_name}. Nuestro equipo se contactará "
                    f"contigo pronto para ofrecer nuevas opciones de horario. ¡Gracias!"
                )
            elif action == "cancel":
                reply = (
                    f"Tu cita ha sido cancelada. Si en el futuro necesitas agendar otra, "
                    f"contáctanos. ¡Que te recuperes!"
                )
        else:
            # Si no se entiende la respuesta, mostrar opciones
            reply = (
                f"Disculpa {appointment.patient.first_name}, no entendí tu respuesta. "
                f"Por favor responde:\n"
                f"• CONFIRMAR\n"
                f"• REPROGRAMAR\n"
                f"• CANCELAR"
            )

        # Enviar respuesta (con logging integrado)
        send_whatsapp_message(f"whatsapp:{e164}", reply, appointment=appointment)
        return Response({"ok": True})
