from django.contrib import admin

from .models import Appointment, AppointmentAction


class AppointmentActionInline(admin.TabularInline):
    model = AppointmentAction
    extra = 0
    readonly_fields = ("created_at",)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "room", "start_datetime", "status")
    list_filter = ("status", "doctor", "room")
    search_fields = ("patient__first_name", "patient__last_name")
    inlines = [AppointmentActionInline]

@admin.register(AppointmentAction)
class AppointmentActionAdmin(admin.ModelAdmin):
    list_display = ("appointment", "action", "created_at")
    list_filter = ("action",)
