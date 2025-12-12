from apps.appointments.models import (Appointment, AppointmentAction,
                                      AppointmentStatus)
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, views
from rest_framework.response import Response

from .models import Notification
from .services import send_whatsapp_message


class SendReminderView(views.APIView):
    def post(self, request, appointment_id: int):
        appointment = Appointment.objects.get(id=appointment_id)
        to = f"whatsapp:{appointment.patient.phone_number}"
        body = (
            f"Hola {appointment.patient.first_name}, tu cita con {appointment.doctor.first_name} "
            f"es el {appointment.start_datetime.strftime('%Y/%m/%d a las %H:%M')}. "
            "Responde: Confirmar / Reprogramar / Cancelar"
        )
        sid = send_whatsapp_message(to, body)
        Notification.objects.create(
            appointment=appointment,
            to=to,
            template="reminder_freeform",
            status="queued",
            external_id=sid,
        )
        return Response({"message_sid": sid})


@method_decorator(csrf_exempt, name="dispatch")
class WhatsAppWebhookView(views.APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        from_number = request.data.get("From")  # whatsapp:+123...
        body = (request.data.get("Body") or "").strip().lower()
        # Find patient by phone (strip prefix)
        e164 = from_number.replace("whatsapp:", "") if from_number else None
        appointment = (
            Appointment.objects.filter(patient__phone_number=e164).order_by("-start_datetime").first()
        )
        if not appointment:
            return Response({"detail": "No appointment found"}, status=status.HTTP_404_NOT_FOUND)

        action = None
        if "confirm" in body or "confirmar" in body:
            appointment.status = AppointmentStatus.CONFIRMED
            action = "confirm"
        elif "reprogram" in body or "reprogramar" in body:
            appointment.status = AppointmentStatus.RESCHEDULED
            action = "reprogram"
        elif "cancel" in body or "cancelar" in body:
            appointment.status = AppointmentStatus.CANCELLED
            action = "cancel"

        if action:
            appointment.save()
            AppointmentAction.objects.create(
                appointment=appointment, action=action, payload={"from": from_number, "body": body}
            )
            reply = (
                "Tu respuesta fue registrada. Gracias."
                if action == "confirm"
                else "Recibimos tu solicitud, el equipo te contactará para reprogramar/cancelar."
            )
        else:
            reply = "Por favor responde: Confirmar / Reprogramar / Cancelar"

        send_whatsapp_message(f"whatsapp:{e164}", reply)
        return Response({"ok": True})
