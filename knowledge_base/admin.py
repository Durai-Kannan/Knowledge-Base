from django.contrib import admin
from .models import URLDocument, DocumentChunk

class DocumentChunkInline(admin.TabularInline):
    model = DocumentChunk
    extra = 0
    fields = ['chunk_index', 'content_preview', 'embedding_id']
    readonly_fields = ['content_preview']

    def content_preview(self, obj):
        return obj.content[:100] + ("..." if len(obj.content) > 100 else "")
    content_preview.short_description = "Content Preview"


@admin.register(URLDocument)
class URLDocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'url', 'http_status', 'title', 'status', 'scraped_at']
    list_filter = ['status', 'http_status', 'scraped_at']
    search_fields = ['url', 'title', 'cleaned_text']
    readonly_fields = ['scraped_at', 'content_hash']
    inlines = [DocumentChunkInline]


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ['id', 'document', 'chunk_index', 'embedding_id', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'document__url']
