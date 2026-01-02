from rest_framework import serializers

from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            'id',
            'first_name',
            'last_name',
            'document_type',
            'document_number',
            'birth_date',
            'phone_number',
            'email',
            'address',
            'company',
            'insurance_provider',
            'insurance_number',
            'emergency_contact',
            'emergency_phone',
            'created_at',
            'updated_at',
            'full_name',
        ]
        read_only_fields = ['company', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
