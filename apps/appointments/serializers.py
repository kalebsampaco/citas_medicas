from rest_framework import serializers

from .models import Appointment, AppointmentAction


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.__str__", read_only=True)
    doctor_name = serializers.CharField(source="doctor.__str__", read_only=True)
    room_name = serializers.CharField(source="room.__str__", read_only=True)

    class Meta:
        model = Appointment
        fields = "__all__"

class AppointmentActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentAction
        fields = "__all__"
