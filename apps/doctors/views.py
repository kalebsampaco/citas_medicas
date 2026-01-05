from apps.accounts.permissions import IsCompanyAdminOrReadOnly
from rest_framework import viewsets

from .models import Doctor
from .serializers import DoctorSerializer


class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsCompanyAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if not getattr(user, 'company_id', None):
            return Doctor.objects.none()
        return Doctor.objects.filter(company=user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, created_by=self.request.user)
