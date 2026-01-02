from django.db import models


class AuditLog(models.Model):
    """Registra todos los cambios realizados en la aplicación"""
    ACTION_CHOICES = [
        ('CREATE', 'Creación'),
        ('UPDATE', 'Actualización'),
        ('DELETE', 'Eliminación'),
    ]

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name='Usuario'
    )
    model_name = models.CharField(max_length=100, verbose_name='Modelo')
    object_id = models.CharField(max_length=50, verbose_name='ID del objeto')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='Acción')
    changes = models.JSONField(default=dict, verbose_name='Cambios')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='Dirección IP')
    user_agent = models.TextField(null=True, blank=True, verbose_name='User Agent')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')

    def __str__(self):
        return f"{self.action} - {self.model_name} ({self.object_id}) - {self.created_at}"

    class Meta:
        verbose_name = 'Registro de auditoría'
        verbose_name_plural = 'Registros de auditoría'
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['user', '-created_at']),
        ]


class EndpointLog(models.Model):
    """Log de uso de endpoints HTTP."""
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='endpoint_logs')
    company = models.ForeignKey('accounts.Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='endpoint_logs')
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    status_code = models.IntegerField()
    duration_ms = models.FloatField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    request_body = models.JSONField(null=True, blank=True)
    response_body = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'endpoint_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['path']),
            models.Index(fields=['method']),
            models.Index(fields=['status_code']),
            models.Index(fields=['company', '-created_at']),
        ]


class TwilioLog(models.Model):
    """Registra envíos y respuestas de Twilio/WhatsApp"""
    DIRECTION_CHOICES = [
        ('OUTBOUND', 'Saliente'),
        ('INBOUND', 'Entrante'),
    ]

    STATUS_CHOICES = [
        ('queued', 'En cola'),
        ('sending', 'Enviando'),
        ('sent', 'Enviado'),
        ('delivered', 'Entregado'),
        ('read', 'Leído'),
        ('failed', 'Fallido'),
        ('undelivered', 'No entregado'),
    ]

    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES,
        verbose_name='Dirección'
    )
    message_sid = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name='SID del mensaje'
    )
    from_number = models.CharField(max_length=50, verbose_name='Desde')
    to_number = models.CharField(max_length=50, verbose_name='Para')
    body = models.TextField(verbose_name='Contenido')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='queued',
        verbose_name='Estado'
    )
    notification = models.ForeignKey(
        'notifications.Notification',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='twilio_logs',
        verbose_name='Notificación'
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='twilio_logs',
        verbose_name='Cita'
    )
    response_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Datos de respuesta'
    )
    error_code = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Código de error'
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        verbose_name='Mensaje de error'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')

    def __str__(self):
        return f"{self.direction} - {self.message_sid} ({self.status})"

    class Meta:
        verbose_name = 'Log de Twilio'
        verbose_name_plural = 'Logs de Twilio'
        db_table = 'twilio_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['direction', '-created_at']),
        ]
