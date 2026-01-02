"""
Plantillas de mensajes de WhatsApp para citas médicas.
Cada plantilla es un diccionario con la estructura del mensaje.
"""

MESSAGE_TEMPLATES = {
    "appointment_created": {
        "name": "appointment_created",
        "subject": "Cita Confirmada",
        "body": (
            "¡Hola {patient_name}!\n\n"
            "Tu cita ha sido confirmada:\n\n"
            "📅 Fecha: {appointment_date}\n"
            "🕐 Hora: {appointment_time}\n"
            "👨‍⚕️ Médico: {doctor_name}\n"
            "🏥 Clínica: {clinic_name}\n\n"
            "Si necesitas cambiar tu cita, responde:\n"
            "• CONFIRMAR\n"
            "• REPROGRAMAR\n"
            "• CANCELAR\n\n"
            "¿Preguntas? Contáctanos."
        ),
        "expected_responses": ["confirmar", "reprogramar", "cancelar"]
    },
    "appointment_reminder_48h": {
        "name": "appointment_reminder_48h",
        "subject": "Recordatorio de Cita",
        "body": (
            "¡Hola {patient_name}!\n\n"
            "Recordatorio: Tu cita es en 2 días 📅\n\n"
            "📅 Fecha: {appointment_date}\n"
            "🕐 Hora: {appointment_time}\n"
            "👨‍⚕️ Médico: {doctor_name}\n"
            "🏥 Clínica: {clinic_name}\n\n"
            "Por favor confirma tu asistencia:\n"
            "• CONFIRMAR - Estaré en la cita\n"
            "• REPROGRAMAR - Necesito otro horario\n"
            "• CANCELAR - No podré asistir\n\n"
            "¡Gracias!"
        ),
        "expected_responses": ["confirmar", "reprogramar", "cancelar"]
    },
    "appointment_reminder_24h": {
        "name": "appointment_reminder_24h",
        "subject": "Tu cita es mañana",
        "body": (
            "¡Hola {patient_name}!\n\n"
            "Último recordatorio: Tu cita es MAÑANA 🕐\n\n"
            "📅 Fecha: {appointment_date}\n"
            "🕐 Hora: {appointment_time}\n"
            "👨‍⚕️ Médico: {doctor_name}\n"
            "🏥 Clínica: {clinic_name}\n\n"
            "¿Todo listo? Responde CONFIRMAR o comunícate con nosotros."
        ),
        "expected_responses": ["confirmar", "reprogramar", "cancelar"]
    },
    "appointment_confirmed": {
        "name": "appointment_confirmed",
        "subject": "Cita Confirmada",
        "body": (
            "¡Excelente {patient_name}!\n\n"
            "Tu cita está confirmada para:\n"
            "📅 {appointment_date}\n"
            "🕐 {appointment_time}\n\n"
            "Nos vemos pronto. Si tienes dudas, contáctanos."
        ),
        "expected_responses": []
    },
    "appointment_rescheduled": {
        "name": "appointment_rescheduled",
        "subject": "Cita Reprogramada",
        "body": (
            "Hola {patient_name},\n\n"
            "Tu solicitud de reprogramación ha sido recibida.\n"
            "Nuestro equipo se contactará pronto con disponibilidad de horarios.\n\n"
            "Gracias por tu comprensión."
        ),
        "expected_responses": []
    },
    "appointment_cancelled": {
        "name": "appointment_cancelled",
        "subject": "Cita Cancelada",
        "body": (
            "Hola {patient_name},\n\n"
            "Tu cita ha sido cancelada.\n"
            "Si deseas agendar una nueva cita, contáctanos.\n\n"
            "¡Que te recuperes pronto!"
        ),
        "expected_responses": []
    }
}


def render_template(template_name: str, context: dict) -> str:
    """
    Renderiza una plantilla con los datos del contexto.

    Args:
        template_name: Nombre de la plantilla (clave en MESSAGE_TEMPLATES)
        context: Diccionario con variables para reemplazar

    Returns:
        str: Mensaje renderizado

    Example:
        context = {
            'patient_name': 'Juan',
            'appointment_date': '2025-01-15',
            'appointment_time': '14:30',
            'doctor_name': 'Dr. López',
            'clinic_name': 'Clínica Central'
        }
        mensaje = render_template('appointment_created', context)
    """
    if template_name not in MESSAGE_TEMPLATES:
        raise ValueError(f"Plantilla '{template_name}' no encontrada")

    template = MESSAGE_TEMPLATES[template_name]
    body = template["body"]

    # Reemplazar variables en formato {variable}
    return body.format(**context)


def get_template_expected_responses(template_name: str) -> list:
    """
    Retorna las respuestas esperadas para una plantilla.
    """
    if template_name in MESSAGE_TEMPLATES:
        return MESSAGE_TEMPLATES[template_name]["expected_responses"]
    return []


def normalize_response(response: str) -> str:
    """
    Normaliza la respuesta del usuario para comparación.
    Convierte a minúsculas y elimina espacios.
    """
    return response.strip().lower()


def parse_user_response(response: str, template_name: str) -> str | None:
    """
    Analiza la respuesta del usuario y retorna la acción identificada.

    Args:
        response: Texto de la respuesta del usuario
        template_name: Nombre de la plantilla para obtener respuestas esperadas

    Returns:
        str: La acción identificada ('confirmar', 'reprogramar', 'cancelar') o None

    Example:
        action = parse_user_response("CONFIRMAR", "appointment_reminder_48h")
        # Retorna: "confirmar"
    """
    normalized = normalize_response(response)

    # Palabras clave para cada acción
    confirm_keywords = ["confirmar", "confirm", "si", "yes", "ok", "vale", "bueno"]
    reschedule_keywords = ["reprogramar", "reschedule", "reprograma", "otro", "cambiar", "otro horario"]
    cancel_keywords = ["cancelar", "cancel", "no", "nope"]

    if any(keyword in normalized for keyword in confirm_keywords):
        return "confirm"
    elif any(keyword in normalized for keyword in reschedule_keywords):
        return "reschedule"
    elif any(keyword in normalized for keyword in cancel_keywords):
        return "cancel"

    return None
