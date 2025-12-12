from django.contrib import admin

from .models import Schedule


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("doctor", "room", "date", "start_time", "end_time", "slot_minutes")
    list_filter = ("date", "doctor", "room")
    search_fields = ("doctor__first_name", "doctor__last_name")
