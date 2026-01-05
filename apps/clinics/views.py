from apps.accounts.permissions import (IsCompanyAdminOrReadOnly,
                                       IsPaymentActiveOrSuperAdmin)
from rest_framework import serializers, viewsets

from .models import Clinic, Room
from .serializers import ClinicSerializer, RoomSerializer


class ClinicViewSet(viewsets.ModelViewSet):
    serializer_class = ClinicSerializer
    permission_classes = [IsCompanyAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        company = getattr(user, "company", None)
        if not getattr(user, "company_id", None):
            return Clinic.objects.none()

        # Ensure each company always has a default clinic so the UI has an option to preselect.
        if not Clinic.objects.filter(company=company).exists():
            Clinic.objects.get_or_create(
                company=company,
                defaults={
                    "name": company.name,
                    "address": company.address or "",
                    "phone_number": company.phone or "",
                },
            )

        return Clinic.objects.filter(company=company)

    def perform_create(self, serializer):
        company = self.request.user.company
        # Validar límite de clínicas
        if company.is_clinics_over_limit:
            raise serializers.ValidationError(
                f"Límite de clínicas alcanzado. Plan permite máximo {company.clinic_limit} clínicas."
            )
        serializer.save(company=company)

class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [IsCompanyAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if not getattr(user, "company_id", None):
            return Room.objects.none()
        return Room.objects.filter(clinic__company=user.company)

    def perform_create(self, serializer):
        serializer.save()
