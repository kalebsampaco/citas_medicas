from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

from .models import AuditLog, TwilioLog


def log_model_change(
    instance: Model,
    action: str,
    user=None,
    changes: dict = None,
    ip_address: str = None,
    user_agent: str = None
):
    """
    Registra un cambio en cualquier modelo de la aplicación.

    Args:
        instance: Instancia del modelo que cambió
        action: 'CREATE', 'UPDATE', o 'DELETE'
        user: Usuario que realizó el cambio
        changes: Diccionario con los cambios realizados
        ip_address: IP desde donde se realizó el cambio
        user_agent: User agent del cliente
    """
    AuditLog.objects.create(
        user=user,
        model_name=instance.__class__.__name__,
        object_id=str(instance.pk),
        action=action,
        changes=changes or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )


def get_model_changes(old_instance, new_instance):
    """
    Compara dos instancias del mismo modelo y retorna los cambios.

    Returns:
        dict: {field_name: {'old': old_value, 'new': new_value}}
    """
    if not old_instance or not new_instance:
        return {}

    changes = {}
    for field in new_instance._meta.fields:
        field_name = field.name
        old_value = getattr(old_instance, field_name, None)
        new_value = getattr(new_instance, field_name, None)

        if old_value != new_value:
            changes[field_name] = {
                'old': str(old_value) if old_value is not None else None,
                'new': str(new_value) if new_value is not None else None,
            }

    return changes


def log_twilio_outbound(
    message_sid: str,
    from_number: str,
    to_number: str,
    body: str,
    status: str = 'queued',
    notification=None,
    appointment=None,
    response_data: dict = None
):
    """
    Registra un mensaje saliente de Twilio.

    Args:
        message_sid: SID del mensaje de Twilio
        from_number: Número desde el que se envía
        to_number: Número al que se envía
        body: Contenido del mensaje
        status: Estado del mensaje
        notification: Instancia de Notification relacionada
        appointment: Instancia de Appointment relacionada
        response_data: Datos completos de la respuesta de Twilio
    """
    return TwilioLog.objects.create(
        direction='OUTBOUND',
        message_sid=message_sid,
        from_number=from_number,
        to_number=to_number,
        body=body,
        status=status,
        notification=notification,
        appointment=appointment,
        response_data=response_data,
    )


def log_twilio_inbound(
    message_sid: str,
    from_number: str,
    to_number: str,
    body: str,
    appointment=None,
    response_data: dict = None
):
    """
    Registra un mensaje entrante de Twilio.

    Args:
        message_sid: SID del mensaje de Twilio
        from_number: Número desde el que se recibe
        to_number: Número al que llega
        body: Contenido del mensaje
        appointment: Instancia de Appointment relacionada
        response_data: Datos completos del webhook
    """
    return TwilioLog.objects.create(
        direction='INBOUND',
        message_sid=message_sid,
        from_number=from_number,
        to_number=to_number,
        body=body,
        status='delivered',  # Los mensajes entrantes ya fueron entregados
        appointment=appointment,
        response_data=response_data,
    )


def update_twilio_status(message_sid: str, status: str, error_code: str = None, error_message: str = None):
    """
    Actualiza el estado de un mensaje de Twilio.

    Args:
        message_sid: SID del mensaje
        status: Nuevo estado
        error_code: Código de error si aplica
        error_message: Mensaje de error si aplica
    """
    try:
        log = TwilioLog.objects.get(message_sid=message_sid)
        log.status = status
        if error_code:
            log.error_code = error_code
        if error_message:
            log.error_message = error_message
        log.save(update_fields=['status', 'error_code', 'error_message', 'updated_at'])
        return log
    except TwilioLog.DoesNotExist:
        return None


def get_client_ip(request):
    """Obtiene la IP del cliente desde el request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Obtiene el user agent del request."""
    return request.META.get('HTTP_USER_AGENT', '')
