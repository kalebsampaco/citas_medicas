from rest_framework import serializers

from .models import ChatActionLog, ChatMessage, ChatSession


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "session", "role", "content", "action", "action_data", "created_at"]
        read_only_fields = ["id", "session", "action", "action_data", "created_at"]


class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ["id", "title", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ChatActionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatActionLog
        fields = [
            "id",
            "session",
            "message",
            "user",
            "raw_content",
            "action",
            "action_data",
            "result",
            "created_at",
        ]
        read_only_fields = fields
