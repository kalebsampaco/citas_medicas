from apps.accounts.permissions import IsCompanyAdminOrReadOnly
from rest_framework import filters, viewsets

from .models import Patient
from .serializers import PatientSerializer


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsCompanyAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["first_name", "last_name", "document_number", "phone_number", "email"]

    def get_queryset(self):
        user = self.request.user
        if not getattr(user, 'company_id', None):
            return Patient.objects.none()
        return Patient.objects.filter(company=user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, created_by=self.request.user)
