from rest_framework import permissions, viewsets

from .models import Patient
from .serializers import PatientSerializer


class IsAdminOrOperator(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ("ADMIN", "OPERATOR"))

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAdminOrOperator]
