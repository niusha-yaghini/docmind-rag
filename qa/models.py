from django.db import models


class QueryLog(models.Model):
    """One question/answer round trip, kept as history."""

    question = models.TextField()
    answer = models.TextField()
    # [{"document_id", "title", "chunk_index", "score", "snippet", optional "rerank_score"}, ...]
    sources = models.JSONField(default=list, blank=True)
    model = models.CharField(max_length=255, blank=True)
    latency_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.question[:80]
