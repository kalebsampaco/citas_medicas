from django.conf import settings
from twilio.rest import Client

from apps.audit.services import log_twilio_outbound


def send_whatsapp_message(
    to_whatsapp: str,
    body: str,
    status_callback: str | None = None,
    notification=None,
    appointment=None
):
    """
    Envía un mensaje de WhatsApp a través de Twilio y registra el log.

    Args:
        to_whatsapp: Número destino en formato 'whatsapp:+1234567890'
        body: Contenido del mensaje
        status_callback: URL para callbacks de estado
        notification: Instancia de Notification relacionada
        appointment: Instancia de Appointment relacionada

    Returns:
        str: SID del mensaje de Twilio
    """
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    sender = settings.TWILIO_WHATSAPP_SENDER
    client = Client(account_sid, auth_token)

    kwargs = {
        "from_": sender,
        "to": to_whatsapp,
        "body": body,
    }
    if status_callback:
        kwargs["status_callback"] = status_callback

    try:
        message = client.messages.create(**kwargs)

        # Registrar el log del mensaje saliente
        log_twilio_outbound(
            message_sid=message.sid,
            from_number=sender,
            to_number=to_whatsapp,
            body=body,
            status=message.status,
            notification=notification,
            appointment=appointment,
            response_data={
                'sid': message.sid,
                'status': message.status,
                'date_created': str(message.date_created),
                'price': message.price,
                'price_unit': message.price_unit,
            }
        )

        return message.sid

    except Exception as e:
        # Registrar el error en el log
        log_twilio_outbound(
            message_sid=f"error_{to_whatsapp}",
            from_number=sender,
            to_number=to_whatsapp,
            body=body,
            status='failed',
            notification=notification,
            appointment=appointment,
            response_data={'error': str(e)}
        )
        raise
