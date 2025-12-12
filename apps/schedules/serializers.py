from rest_framework import serializers

from .models import Schedule


class ScheduleSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="doctor.__str__", read_only=True)
    room_name = serializers.CharField(source="room.__str__", read_only=True)

    class Meta:
        model = Schedule
        fields = "__all__"
