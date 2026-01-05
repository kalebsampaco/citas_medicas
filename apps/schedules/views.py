from apps.accounts.permissions import IsPaymentActiveOrSuperAdmin
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Schedule
from .serializers import ScheduleSerializer


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    filterset_fields = ["doctor", "room", "date", "is_available"]
    permission_classes = [IsAuthenticated, IsPaymentActiveOrSuperAdmin]

    def get_queryset(self):
        user = self.request.user
        if not getattr(user, 'company_id', None):
            return Schedule.objects.none()
        return Schedule.objects.filter(doctor__company=user.company)

    def perform_create(self, serializer):
        # Si no viene clinic, usar la del doctor
        doctor = serializer.validated_data.get('doctor')
        clinic = serializer.validated_data.get('clinic')

        if not clinic and doctor and getattr(doctor, 'clinic_id', None):
            serializer.validated_data['clinic'] = doctor.clinic

        serializer.save()
