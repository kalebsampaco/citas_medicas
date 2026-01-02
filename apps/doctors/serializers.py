from apps.clinics.models import Room
from rest_framework import serializers

from .models import Doctor


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = "__all__"
        extra_kwargs = {
            "company": {"read_only": True},
            "created_by": {"read_only": True},
            "room": {"required": True, "allow_null": False},
        }

    def validate_room(self, room: Room):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and getattr(user, "company_id", None):
            if room and room.clinic.company_id != user.company_id:
                raise serializers.ValidationError("El consultorio no pertenece a tu empresa")
        return room

    def validate(self, attrs):
        if not attrs.get("room"):
            raise serializers.ValidationError({"room": "Debes asignar un consultorio"})
        return super().validate(attrs)
