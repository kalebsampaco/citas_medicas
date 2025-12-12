from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Appointment, AppointmentAction
from .serializers import AppointmentActionSerializer, AppointmentSerializer


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    filterset_fields = ["patient", "doctor", "room", "status"]

    @action(detail=True, methods=["get"])
    def actions(self, request, pk=None):
        appointment = self.get_object()
        actions = appointment.actions.all()
        serializer = AppointmentActionSerializer(actions, many=True)
        return Response(serializer.data)
