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
        serializer.save()
