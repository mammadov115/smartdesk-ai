from rest_framework import serializers


class ConversationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    message_count = serializers.IntegerField()
    first_message_at = serializers.DateTimeField(allow_null=True)
    last_message_at = serializers.DateTimeField(allow_null=True)
    duration_seconds = serializers.IntegerField(allow_null=True)


class MessageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    role = serializers.CharField()
    content = serializers.CharField()
    sources = serializers.ListField(child=serializers.DictField())
    created_at = serializers.DateTimeField()


class ConversationDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    message_count = serializers.IntegerField()
    messages = MessageSerializer(many=True)


class MostAskedQuestionSerializer(serializers.Serializer):
    question = serializers.CharField()
    count = serializers.IntegerField()


class UnansweredQuestionSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    question = serializers.CharField()
    asked_at = serializers.DateTimeField()
    session_created_at = serializers.DateTimeField()


class StatsSerializer(serializers.Serializer):
    period = serializers.DateTimeField()
    conversations = serializers.IntegerField()
    messages = serializers.IntegerField()
