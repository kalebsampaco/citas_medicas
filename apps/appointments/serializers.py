from apps.clinics.models import Room
from apps.doctors.models import Doctor
from apps.patients.models import Patient
from apps.schedules.models import Schedule
from django.db.models import Q
from rest_framework import serializers

from .models import Appointment, AppointmentAction


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.__str__", read_only=True)
    doctor_name = serializers.CharField(source="doctor.__str__", read_only=True)
    clinic_name = serializers.CharField(source="clinic.__str__", read_only=True)
    room_name = serializers.CharField(source="room.__str__", read_only=True)
    # Alias de escritura para compatibilidad con el frontend
    clinicId = serializers.IntegerField(write_only=True, required=False)
    patientId = serializers.IntegerField(write_only=True, required=False)
    doctorId = serializers.IntegerField(write_only=True, required=False)
    roomId = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Appointment
        fields = "__all__"
        extra_kwargs = {
            # Permitimos omitirlos en payload; se completan en validate()
            'clinic': { 'required': False },
            'patient': { 'required': False },
            'doctor': { 'required': False },
            'room': { 'required': False, 'allow_null': True },
            'schedule': { 'required': False },
        }

    def validate(self, attrs):
        data = getattr(self, 'initial_data', {}) or {}

        # Mapear alias *_Id si el cliente los envía
        if not attrs.get('clinic') and data.get('clinicId'):
            from apps.clinics.models import Clinic
            try:
                attrs['clinic'] = Clinic.objects.get(pk=data.get('clinicId'))
            except Clinic.DoesNotExist:
                raise serializers.ValidationError({'clinicId': 'Clínica no encontrada'})

        if not attrs.get('patient') and data.get('patientId'):
            try:
                attrs['patient'] = Patient.objects.get(pk=data.get('patientId'))
            except Patient.DoesNotExist:
                raise serializers.ValidationError({'patientId': 'Paciente no encontrado'})

        if not attrs.get('doctor') and data.get('doctorId'):
            try:
                attrs['doctor'] = Doctor.objects.get(pk=data.get('doctorId'))
            except Doctor.DoesNotExist:
                raise serializers.ValidationError({'doctorId': 'Médico no encontrado'})

        if not attrs.get('room') and data.get('roomId'):
            try:
                attrs['room'] = Room.objects.get(pk=data.get('roomId'))
            except Room.DoesNotExist:
                raise serializers.ValidationError({'roomId': 'Consultorio no encontrado'})

        clinic = attrs.get('clinic')
        doctor = attrs.get('doctor')
        room = attrs.get('room')
        start = attrs.get('start_datetime')
        end = attrs.get('end_datetime')

        # Si no viene clinic, usar la del médico si existe
        if not clinic and doctor and getattr(doctor, 'clinic_id', None):
            attrs['clinic'] = doctor.clinic
            clinic = attrs['clinic']

        # Si no viene room, usar el del médico si existe
        if not room and doctor and getattr(doctor, 'room_id', None):
            attrs['room'] = doctor.room
            room = attrs['room']

        # Resolver schedule automáticamente según rango de tiempo
        if doctor and start and end:
            qs = Schedule.objects.filter(doctor=doctor, date=start.date(), is_available=True)
            if clinic:
                qs = qs.filter(clinic=clinic)
            if room:
                qs = qs.filter(Q(room__isnull=True) | Q(room=room))

            # Mantener solo los que cubren el rango solicitado
            slots = [s for s in qs if s.start_time <= start.time() and end.time() <= s.end_time]
            if not slots:
                raise serializers.ValidationError({'schedule': 'No hay horario disponible para ese rango'})
            attrs['schedule'] = slots[0]

        return attrs

    def create(self, validated_data):
        # Remover alias que no pertenecen al modelo
        validated_data.pop('clinicId', None)
        validated_data.pop('patientId', None)
        validated_data.pop('doctorId', None)
        validated_data.pop('roomId', None)
        return super().create(validated_data)

class AppointmentActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentAction
        fields = "__all__"
