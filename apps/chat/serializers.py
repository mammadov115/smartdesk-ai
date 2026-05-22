from rest_framework import serializers

from .models import ChatMessage, ChatSession


class ChatSessionSerializer(serializers.ModelSerializer):
    chat_name = serializers.SerializerMethodField()
    greeting_message = serializers.SerializerMethodField()
    chat_language = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "status",
            "chat_name",
            "greeting_message",
            "chat_language",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "chat_name",
            "greeting_message",
            "chat_language",
            "created_at",
        ]

    def get_chat_name(self, obj) -> str:
        try:
            return obj.owner.company_profile.chat_name
        except Exception:
            return "AI Assistant"

    def get_greeting_message(self, obj) -> str:
        try:
            return obj.owner.company_profile.greeting_message
        except Exception:
            return ""

    def get_chat_language(self, obj) -> str:
        try:
            return obj.owner.company_profile.chat_language
        except Exception:
            return ""


class AskSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=2000, trim_whitespace=True)


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "sources", "created_at"]
        read_only_fields = fields
