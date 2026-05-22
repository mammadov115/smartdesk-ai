from rest_framework import serializers

from .models import KnowledgeDocument


class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    # For FAQ uploads only
    question = serializers.CharField(write_only=True, required=False)
    answer = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = KnowledgeDocument
        fields = [
            "id",
            "title",
            "source_type",
            "file",
            "raw_text",
            "question",
            "answer",
            "status",
            "error_message",
            "created_at",
        ]
        read_only_fields = ["status", "error_message", "created_at"]

    def validate(self, attrs):
        source_type = attrs.get("source_type")
        file = attrs.get("file")
        raw_text = attrs.get("raw_text", "")
        question = attrs.pop("question", "")
        answer = attrs.pop("answer", "")

        if source_type == KnowledgeDocument.SourceType.FAQ:
            if not question or not answer:
                raise serializers.ValidationError("Both 'question' and 'answer' are required for FAQ entries.")
            attrs["raw_text"] = f"Q: {question}\nA: {answer}"

        elif source_type in (
            KnowledgeDocument.SourceType.PDF,
            KnowledgeDocument.SourceType.DOCX,
            KnowledgeDocument.SourceType.TXT,
        ):
            if not file:
                raise serializers.ValidationError(f"A file is required for source_type '{source_type}'.")

        elif source_type == KnowledgeDocument.SourceType.TEXT:
            if not raw_text.strip():
                raise serializers.ValidationError("'raw_text' is required for source_type 'text'.")

        return attrs
