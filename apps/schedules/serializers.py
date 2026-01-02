from apps.clinics.models import Room
from apps.doctors.models import Doctor
from rest_framework import serializers

from .models import Schedule


class ScheduleSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="doctor.__str__", read_only=True)
    room_name = serializers.CharField(source="room.__str__", read_only=True)

    class Meta:
        model = Schedule
        fields = ["id", "doctor", "doctor_name", "room", "room_name", "date", "start_time", "end_time", "slot_minutes", "is_available", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {
            "room": {"required": False, "allow_null": True}
        }

    def validate(self, attrs):
        doctor: Doctor = attrs.get("doctor")
        room: Room = attrs.get("room")
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if user and getattr(user, "company_id", None):
            if doctor and doctor.company_id != user.company_id:
                raise serializers.ValidationError({"doctor": "El médico no pertenece a tu empresa"})
            if room and room.clinic.company_id != user.company_id:
                raise serializers.ValidationError({"room": "El consultorio no pertenece a tu empresa"})

        # Si el doctor tiene consultorio asignado, forzar a usarlo
        if doctor and doctor.room:
            if room and room.id != doctor.room_id:
                raise serializers.ValidationError({"room": "El horario debe usar el consultorio asignado al médico"})
            attrs["room"] = doctor.room

        return super().validate(attrs)
