from django.contrib import admin

from .models import AuditLog, TwilioLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'action', 'model_name', 'object_id', 'user', 'created_at')
    list_filter = ('action', 'model_name', 'created_at')
    search_fields = ('model_name', 'object_id', 'user__email', 'user__username')
    readonly_fields = ('user', 'model_name', 'object_id', 'action', 'changes', 'ip_address', 'user_agent', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        # No permitir crear logs manualmente
        return False

    def has_change_permission(self, request, obj=None):
        # No permitir editar logs
        return False

    def has_delete_permission(self, request, obj=None):
        # Solo superusuarios pueden eliminar
        return request.user.is_superuser


@admin.register(TwilioLog)
class TwilioLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'direction', 'message_sid', 'from_number', 'to_number', 'status', 'created_at')
    list_filter = ('direction', 'status', 'created_at')
    search_fields = ('message_sid', 'from_number', 'to_number', 'body')
    readonly_fields = (
        'direction', 'message_sid', 'from_number', 'to_number', 'body',
        'status', 'notification', 'appointment', 'response_data',
        'error_code', 'error_message', 'created_at', 'updated_at'
    )
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        ('Información del Mensaje', {
            'fields': ('direction', 'message_sid', 'from_number', 'to_number', 'body', 'status')
        }),
        ('Relaciones', {
            'fields': ('notification', 'appointment')
        }),
        ('Detalles Técnicos', {
            'fields': ('response_data', 'error_code', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def has_add_permission(self, request):
        # No permitir crear logs manualmente
        return False

    def has_change_permission(self, request, obj=None):
        # No permitir editar logs
        return False

    def has_delete_permission(self, request, obj=None):
        # Solo superusuarios pueden eliminar
        return request.user.is_superuser
