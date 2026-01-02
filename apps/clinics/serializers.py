from rest_framework import serializers

from .models import Clinic, Room


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = "__all__"
        extra_kwargs = {
            "clinic": {"required": True}
        }

    def validate_clinic(self, clinic):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and getattr(user, "company_id", None):
            if clinic.company_id and clinic.company_id != user.company_id:
                raise serializers.ValidationError("La clínica no pertenece a tu empresa")
            # if clinic has no company set, bind it automatically
            if clinic.company_id is None:
                clinic.company = user.company
                clinic.save()
        return clinic

class ClinicSerializer(serializers.ModelSerializer):
    rooms = RoomSerializer(many=True, read_only=True)

    class Meta:
        model = Clinic
        fields = "__all__"
        read_only_fields = ["company"]
