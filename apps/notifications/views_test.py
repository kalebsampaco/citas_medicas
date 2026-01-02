from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .services import send_whatsapp_message


class TestWhatsAppView(views.APIView):
    """
    Endpoint de prueba para enviar mensajes de WhatsApp a través de Twilio.

    POST /api/notifications/test-whatsapp/
    {
        "phone_number": "+1234567890",
        "message": "Este es un mensaje de prueba"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        phone_number = request.data.get('phone_number')
        message = request.data.get('message', 'Mensaje de prueba desde citas médicas')

        if not phone_number:
            return Response(
                {"error": "phone_number es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Normalizar el número
        if not phone_number.startswith('+'):
            phone_number = f'+{phone_number}'

        to_whatsapp = f"whatsapp:{phone_number}"

        try:
            message_sid = send_whatsapp_message(
                to_whatsapp=to_whatsapp,
                body=message,
                notification=None,
                appointment=None
            )

            return Response({
                "status": "success",
                "message_sid": message_sid,
                "to": to_whatsapp,
                "body": message
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "error",
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
