from django.conf import settings
from django.db import models


class ChatSession(models.Model):
    """Sesión de chat entre un usuario autenticado y la IA."""

    STEP_CHOICES = (
        ("initial", "Inicial: mostrar opciones"),
        ("selecting_action", "Seleccionar acción (agendar/ver agenda)"),
        ("getting_patient_cedula", "Solicitando cédula del paciente"),
        ("selecting_doctor", "Seleccionar médico"),
        ("selecting_date", "Seleccionar fecha"),
        ("confirming_appointment", "Confirmar agendamiento"),
        ("completed", "Completado"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions")
    title = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    current_step = models.CharField(max_length=30, choices=STEP_CHOICES, default="initial")
    context_data = models.JSONField(default=dict, blank=True, help_text="Datos temporales: cedula, doctor_id, date, etc.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chat_sessions"
        ordering = ["-updated_at"]

    def __str__(self) -> str:  # pragma: no cover - representación simple
        return self.title or f"Chat {self.user} - {self.created_at:%Y-%m-%d}"


class ChatMessage(models.Model):
    """Mensaje individual dentro de una sesión."""

    ROLE_CHOICES = (
        ("system", "System"),
        ("user", "User"),
        ("assistant", "Assistant"),
    )

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    action = models.CharField(max_length=50, blank=True, null=True)
    action_data = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_messages"
        ordering = ["created_at"]

    def __str__(self) -> str:  # pragma: no cover - representación simple
        return f"{self.role}: {self.content[:50]}"


class ChatActionLog(models.Model):
    """Registro auditable de las acciones solicitadas a la IA."""

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="action_logs")
    message = models.ForeignKey(ChatMessage, on_delete=models.SET_NULL, null=True, blank=True, related_name="action_logs")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_action_logs")
    raw_content = models.TextField(blank=True)
    action = models.CharField(max_length=50, blank=True, null=True)
    action_data = models.JSONField(default=dict, blank=True, null=True)
    result = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_action_logs"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - representación simple
        return f"{self.action} - {self.created_at:%Y-%m-%d %H:%M:%S}"
