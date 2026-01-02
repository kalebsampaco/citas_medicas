from apps.accounts.permissions import IsPaymentActiveOrSuperAdmin
from rest_framework import filters, permissions, viewsets
from rest_framework.permissions import SAFE_METHODS

from .models import Patient
from .serializers import PatientSerializer


class IsCompanyMember(permissions.BasePermission):
    """Permite acceso a usuarios autenticados con compañía asignada."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, 'company_id', None))

    def has_object_permission(self, request, view, obj):
        user = request.user
        same_company = getattr(user, 'company_id', None) == getattr(obj, 'company_id', None)
        if not same_company:
            return False
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, 'created_by_id', None) == user.id

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsCompanyMember, IsPaymentActiveOrSuperAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ["first_name", "last_name", "document_number", "phone_number", "email"]

    def get_queryset(self):
        user = self.request.user
        if not getattr(user, 'company_id', None):
            return Patient.objects.none()
        return Patient.objects.filter(company=user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, created_by=self.request.user)
