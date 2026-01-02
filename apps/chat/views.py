from apps.accounts.permissions import IsPaymentActiveOrSuperAdmin
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ChatActionLog, ChatMessage, ChatSession
from .serializers import (ChatActionLogSerializer, ChatMessageSerializer,
                          ChatSessionSerializer)
from .services import get_ai_response, process_action


class ChatSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated, IsPaymentActiveOrSuperAdmin]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="send-message")
    def send_message(self, request, pk=None):
        session = self.get_object()
        text = (request.data.get("message") or "").strip()
        if not text:
            return Response({"detail": "message es requerido"}, status=status.HTTP_400_BAD_REQUEST)

        user_msg = ChatMessage.objects.create(session=session, role="user", content=text)

        # DETECCIÓN ANTICIPADA: Si estamos en "selecting_date" y el texto tiene formato "ID|Nombre"
        # procesamos directamente sin llamar al AI
        import re
        pattern = r'^(\d+)\|(.+)$'
        match = re.match(pattern, text)

        if session.current_step == "selecting_date" and match:
            # Extraer doctor_id del formato "ID|Nombre"
            doctor_id = int(match.group(1))
            doctor_name = match.group(2).strip()

            ai_result = {
                "message": f"Confirmando que has seleccionado a {doctor_name}. Mostrando disponibilidad...",
                "action": "select_doctor",
                "action_data": {"doctor_id": doctor_id},
                "raw": text
            }
        else:
            chat_history = list(session.messages.all())
            ai_result = get_ai_response(text, chat_history, request.user, current_step=session.current_step)

        assistant_msg = ChatMessage.objects.create(
            session=session,
            role="assistant",
            content=ai_result.get("message", ""),
            action=ai_result.get("action"),
            action_data=ai_result.get("action_data"),
        )

        action_result = process_action(ai_result.get("action"), ai_result.get("action_data"), request.user, session=session)

        ChatActionLog.objects.create(
            session=session,
            message=assistant_msg,
            user=request.user,
            raw_content=ai_result.get("raw", ai_result.get("message", "")),
            action=ai_result.get("action"),
            action_data=ai_result.get("action_data"),
            result=action_result,
        )

        return Response(
            {
                "user_message": ChatMessageSerializer(user_msg).data,
                "assistant_message": ChatMessageSerializer(assistant_msg).data,
                "action_result": action_result,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="action-logs")
    def action_logs(self, request, pk=None):
        session = self.get_object()
        qs = session.action_logs.all()
        serializer = ChatActionLogSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="messages")
    def list_messages(self, request, pk=None):
        session = self.get_object()
        qs = session.messages.all()
        serializer = ChatMessageSerializer(qs, many=True)
        return Response(serializer.data)
