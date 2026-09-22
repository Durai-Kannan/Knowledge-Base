from rest_framework import serializers
from .models import URLDocument, DocumentChunk

class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = [
            "id",
            "chunk_index",
            "content",
            "embedding_id",
            "metadata",
            "created_at"
        ]


class URLDocumentSerializer(serializers.ModelSerializer):
    chunks_count = serializers.IntegerField(source='chunks.count', read_only=True)

    class Meta:
        model = URLDocument
        fields = [
            "id",
            "url",
            "http_status",
            "title",
            "raw_html",
            "cleaned_text",
            "metadata",
            "content_hash",
            "scraped_at",
            "status",
            "error_message",
            "chunks_count"
        ]


class URLDocumentDetailSerializer(serializers.ModelSerializer):
    chunks = DocumentChunkSerializer(many=True, read_only=True)

    class Meta:
        model = URLDocument
        fields = [
            "id",
            "url",
            "http_status",
            "title",
            "raw_html",
            "cleaned_text",
            "metadata",
            "content_hash",
            "scraped_at",
            "status",
            "error_message",
            "chunks"
        ]
