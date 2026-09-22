from django.db import models

class URLDocument(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    url = models.URLField(max_length=2048, unique=True)
    http_status = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=500, blank=True)
    raw_html = models.TextField(blank=True)
    cleaned_text = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    content_hash = models.CharField(max_length=64, blank=True)
    scraped_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="pending")
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-scraped_at']
        verbose_name = "URL Document"
        verbose_name_plural = "URL Documents"

    def __str__(self):
        return f"{self.url} ({self.status})"


class DocumentChunk(models.Model):
    document = models.ForeignKey(
        URLDocument,
        on_delete=models.CASCADE,
        related_name="chunks"
    )
    chunk_index = models.IntegerField()
    content = models.TextField()
    embedding_id = models.IntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['document', 'chunk_index']
        verbose_name = "Document Chunk"
        verbose_name_plural = "Document Chunks"

    def __str__(self):
        return f"Chunk {self.chunk_index} for Doc {self.document_id}"
