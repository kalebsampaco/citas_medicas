from azure.communication.email import EmailClient
from azure.core.exceptions import AzureError
from django.conf import settings


def send_admin_credentials_email(to_email: str, company_name: str, username: str, password: str) -> bool:
    """
    Envía credenciales iniciales del admin de empresa mediante Azure Communication Services Email.
    """
    if not getattr(settings, "ACS_CONNECTION_STRING", None) or not getattr(settings, "ACS_SENDER_EMAIL", None):
        return False

    client = EmailClient.from_connection_string(settings.ACS_CONNECTION_STRING)

    subject = f"Credenciales de acceso - {company_name}"
    html = f"""
    <div style="font-family:Segoe UI,Arial,sans-serif;">
      <h2>Bienvenido(a) a {company_name}</h2>
      <p>Se ha creado el usuario administrador de su empresa.</p>
      <p><strong>Usuario (email):</strong> {username}<br/>
         <strong>Contraseña temporal:</strong> {password}</p>
      <p>Por seguridad, cambie la contraseña luego de iniciar sesión.</p>
      <hr/>
      <small>Este correo fue enviado automáticamente. No responder.</small>
    </div>
    """
    message = {
        "senderAddress": settings.ACS_SENDER_EMAIL,
        "recipients": {"to": [{"address": to_email}]},
        "content": {"subject": subject, "html": html},
        "attachments": []
    }

    try:
        poller = client.begin_send(message)
        poller.result()  # esperar envío
        return True
    except AzureError:
        return False
