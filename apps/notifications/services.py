from django.conf import settings
from twilio.rest import Client


def send_whatsapp_message(to_whatsapp: str, body: str, status_callback: str | None = None):
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
    message = client.messages.create(**kwargs)
    return message.sid
