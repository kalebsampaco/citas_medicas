"""
GUÍA COMPLETA DE PRUEBA - Sistema de Notificaciones por WhatsApp

Este documento describe cómo probar todo el flujo de automatización de citas.
"""

# ============================================================================
# PARTE 1: PREPARACIÓN
# ============================================================================

"""
1. Asegúrate de que Twilio esté configurado:
   - TWILIO_ACCOUNT_SID en .env ✅
   - TWILIO_AUTH_TOKEN en .env ✅
   - TWILIO_WHATSAPP_SENDER en .env ✅

2. Agrega tu número al sandbox de Twilio:
   - Ve a https://console.twilio.com/us/messaging/whatsapp/learn
   - Sigue las instrucciones para unirte al sandbox
   - Envía: "join PALABRA-CLAVE" al número sandbox

3. Inicia el servidor Django:
   poetry run python manage.py runserver
"""

# ============================================================================
# PARTE 2: CREAR UNA CITA (ACTIVARÁ SIGNAL AUTOMÁTICO)
# ============================================================================

"""
POST /api/appointments/

{
  "patient": "patient-uuid",
  "doctor": 1,
  "room": 1,
  "schedule": 1,
  "start_datetime": "2025-01-15T14:30:00Z",
  "end_datetime": "2025-01-15T15:00:00Z",
  "status": "PENDING",
  "notes": "Revisión de control"
}

RESULTADO ESPERADO:
✅ Se crea la cita
✅ Se envía automáticamente un WhatsApp al paciente con detalles de la cita
   Mensaje: "¡Hola [Nombre]! Tu cita ha sido confirmada..."
✅ Se crea un registro en Notification table
"""

# ============================================================================
# PARTE 3: PROBAR RECORDATORIO 48 HORAS (Command)
# ============================================================================

"""
Simulación manual (para pruebas - la cita debe estar en 48h):

poetry run python manage.py send_appointment_reminders --dry-run

Salida esperada:
[DRY-RUN] Recordatorio 48h para Juan (+507XXXXXXXX) - 2025-01-15 14:30:00

ENVÍO REAL (sin --dry-run):
poetry run python manage.py send_appointment_reminders

Salida esperada:
✅ Recordatorio 48h enviado a +507XXXXXXXX

MENSAJES AUTOMÁTICOS (sin intervention manual):
- El usuario recibe: "Recordatorio: Tu cita es en 2 días..."
- Se solicita confirmación: CONFIRMAR / REPROGRAMAR / CANCELAR
"""

# ============================================================================
# PARTE 4: PROBAR RESPUESTA DEL USUARIO (Webhook)
# ============================================================================

"""
Cuando el usuario responde en WhatsApp con:
- "CONFIRMAR" o "Confirmar" o "Si" o "OK"
- "REPROGRAMAR" o "Otro horario"
- "CANCELAR" o "No"

FLUJO AUTOMÁTICO:
1. Twilio envía webhook a tu servidor
2. El código analiza la respuesta (parse_user_response)
3. Actualiza el estado de la cita automáticamente:
   - CONFIRMAR → status = CONFIRMED
   - REPROGRAMAR → status = RESCHEDULED
   - CANCELAR → status = CANCELLED
4. Se registra en AppointmentAction
5. Se envía respuesta personalizada al usuario

RESPUESTA ESPERADA:
- Si CONFIRMAR: "¡Perfecto! Tu cita está confirmada para [fecha/hora]. ¡Te esperamos!"
- Si REPROGRAMAR: "Entendido. Nuestro equipo se contactará contigo pronto..."
- Si CANCELAR: "Tu cita ha sido cancelada. Si en el futuro necesitas..."
"""

# ============================================================================
# PARTE 5: VERIFICAR REGISTROS EN BASE DE DATOS
# ============================================================================

"""
1. Checa los registros de Notifications:
   SELECT * FROM notifications WHERE appointment_id = X;

   Deberías ver:
   - appointment_created (cuando se crea la cita)
   - appointment_reminder_48h (si pasó el tiempo y corriste el command)
   - appointment_reminder_24h (opcional)

2. Checa los registros de AppointmentAction:
   SELECT * FROM appointmentActions WHERE appointment_id = X;

   Deberías ver:
   - action='confirm' con payload={from: 'whatsapp:+...', body: 'CONFIRMAR'}

3. Checa el cambio de estado en Appointment:
   SELECT status FROM appointments WHERE id = X;

   Debería mostrar: PENDING → CONFIRMED/RESCHEDULED/CANCELLED

4. Checa el log de auditoría (TwilioLog):
   SELECT * FROM twilio_logs WHERE appointment_id = X;

   Deberías ver registros OUTBOUND y INBOUND
"""

# ============================================================================
# PARTE 6: ENDPOINT DE PRUEBA RÁPIDA
# ============================================================================

"""
Si solo quieres probar el envío SIN crear una cita formal:

POST /api/notifications/test-whatsapp/

{
  "phone_number": "+507XXXXXXXX",
  "message": "Hola, esto es una prueba"
}

Respuesta:
{
  "status": "success",
  "message_sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "to": "whatsapp:+507XXXXXXXX",
  "body": "Hola, esto es una prueba"
}

El mensaje llegará a tu WhatsApp en segundos.
"""

# ============================================================================
# PARTE 7: TROUBLESHOOTING
# ============================================================================

"""
PROBLEMA: "No appointment found" en webhook
SOLUCIÓN: Verifica que el phone_number del paciente coincida exactamente

PROBLEMA: No llega el mensaje
SOLUCIÓN:
- Verifica que el número esté en el sandbox de Twilio
- Revisa que TWILIO_AUTH_TOKEN sea correcto
- Mira los logs: python manage.py shell
  >>> from apps.audit.models import TwilioLog
  >>> TwilioLog.objects.last()

PROBLEMA: "duplicate key value violates unique constraint"
SOLUCIÓN: Ya está arreglado con UUID en error messages

PROBLEMA: Señal no se dispara
SOLUCIÓN: Verifica que apps/notifications/apps.py tenga el método ready()
"""

# ============================================================================
# PARTE 8: INSTALACIÓN DE TAREAS PERIÓDICAS (Celery - Opcional)
# ============================================================================

"""
Para automatizar el envío de recordatorios sin correr el command manualmente,
puedes usar Celery + Beat:

1. Instala: pip install celery redis

2. Crea apps/notifications/tasks.py:
   @shared_task
   def send_appointment_reminders_task():
       # Llamar al command
       call_command('send_appointment_reminders')

3. Configura en settings.py:
   CELERY_BEAT_SCHEDULE = {
       'send_reminders_every_hour': {
           'task': 'apps.notifications.tasks.send_appointment_reminders_task',
           'schedule': crontab(minute=0),  # Cada hora
       }
   }

4. Inicia Celery:
   celery -A project worker -l info
   celery -A project beat -l info
"""

# ============================================================================
# CHECKLIST FINAL DE PRUEBA
# ============================================================================

"""
□ Twilio credentials en .env
□ Número agregado al sandbox de Twilio
□ Servidor Django funcionando
□ Se crea una cita y se envía automáticamente mensaje
□ Se recibe el mensaje en WhatsApp
□ Se responde desde WhatsApp (CONFIRMAR/REPROGRAMAR/CANCELAR)
□ Se actualiza el status de la cita automáticamente
□ Se recibe respuesta personalizada en WhatsApp
□ Los registros en DB están correctos (Notification, AppointmentAction, TwilioLog)
□ Command de recordatorios funciona (--dry-run primero)
□ Webhook procesa respuestas correctamente
"""
