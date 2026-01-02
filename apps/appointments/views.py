from apps.accounts.permissions import IsPaymentActiveOrSuperAdmin
from apps.schedules.models import Schedule
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Appointment, AppointmentAction
from .serializers import AppointmentActionSerializer, AppointmentSerializer


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    filterset_fields = ["patient", "doctor", "room", "status"]
    permission_classes = [IsPaymentActiveOrSuperAdmin]
    permission_classes = [IsPaymentActiveOrSuperAdmin]

    def get_queryset(self):
        """Filtrar citas por company del usuario autenticado"""
        user = self.request.user
        company = getattr(user, 'company', None)

        if not user.is_authenticated or not company:
            return Appointment.objects.none()

        # Mostrar todas las citas de la empresa (de cualquier paciente/médico)
        return Appointment.objects.filter(patient__company=company)

    @action(detail=True, methods=["get"])
    def actions(self, request, pk=None):
        appointment = self.get_object()
        actions = appointment.actions.all()
        serializer = AppointmentActionSerializer(actions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def actions(self, request, pk=None):  # type: ignore[override]
        """Create an action on an appointment: confirm, cancel, reschedule."""
        appointment: Appointment = self.get_object()
        action_type = request.data.get("action")
        payload = request.data.get("payload", {})
        reason = request.data.get("reason")

        if action_type not in {"confirm", "cancel", "reschedule"}:
            return Response({"detail": "Acción inválida"}, status=status.HTTP_400_BAD_REQUEST)

        if action_type == "confirm":
            appointment.status = Appointment.Status.CONFIRMED if hasattr(Appointment, "Status") else "CONFIRMED"
            appointment.save()

        elif action_type == "cancel":
            appointment.status = Appointment.Status.CANCELLED if hasattr(Appointment, "Status") else "CANCELLED"
            appointment.save()

        elif action_type == "reschedule":
            new_start = payload.get("start_datetime") or request.data.get("start_datetime")
            if not new_start:
                return Response({"detail": "start_datetime es requerido"}, status=status.HTTP_400_BAD_REQUEST)

            # Encontrar un schedule para la nueva fecha/hora
            # Asumimos que el serializer ya relaciona Appointment con Schedule.
            # Si se requiere selección explícita de schedule, ajustar aquí.
            try:
                new_schedule = Schedule.objects.filter(
                    doctor=appointment.doctor,
                    date=str(new_start).split("T")[0]
                ).first()
            except Exception:
                new_schedule = None

            if not new_schedule:
                return Response({"detail": "No se encontró horario para esa fecha"}, status=status.HTTP_400_BAD_REQUEST)

            old_schedule = appointment.schedule
            appointment.start_datetime = new_start
            appointment.schedule = new_schedule
            appointment.status = Appointment.Status.RESCHEDULED if hasattr(Appointment, "Status") else "RESCHEDULED"
            appointment.save()

            # Actualizar disponibilidad si cambió el schedule
            if old_schedule and old_schedule.id != new_schedule.id:
                if not Appointment.objects.filter(schedule=old_schedule).exists():
                    old_schedule.is_available = True
                    old_schedule.save()
                new_schedule.is_available = False
                new_schedule.save()

        # Registrar acción
        AppointmentAction.objects.create(
            appointment=appointment,
            action=action_type,
            payload=payload or ({"reason": reason} if reason else {})
        )

        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        # Obtener la cita actual antes de actualizar
        old_appointment = self.get_object()
        old_schedule = old_appointment.schedule

        # Guardar la cita actualizada
        new_appointment = serializer.save()
        new_schedule = new_appointment.schedule

        # Si el schedule cambió, liberar el viejo y ocupar el nuevo
        if old_schedule.id != new_schedule.id:
            # Liberar el slot viejo si no hay más citas en ese schedule
            if not Appointment.objects.filter(schedule=old_schedule).exists():
                old_schedule.is_available = True
                old_schedule.save()

            # Marcar el nuevo schedule como no disponible
            new_schedule.is_available = False
            new_schedule.save()
