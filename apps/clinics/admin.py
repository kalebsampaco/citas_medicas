from django.contrib import admin

from .models import Clinic, Room


class RoomInline(admin.TabularInline):
    model = Room
    extra = 1

@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "phone_number")
    search_fields = ("name",)
    inlines = [RoomInline]

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "clinic", "capacity")
    list_filter = ("clinic",)
