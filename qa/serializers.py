from rest_framework import serializers

from qa.models import QueryLog


class AskSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=2000, trim_whitespace=True)


class QueryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryLog
        fields = ["id", "question", "answer", "sources", "model", "latency_ms", "created_at"]
        read_only_fields = fields


class SearchParamsSerializer(serializers.Serializer):
    q = serializers.CharField(max_length=2000, help_text="Search text.")
    k = serializers.IntegerField(required=False, min_value=1, max_value=20, help_text="Number of chunks (default 5).")


class SearchHitSerializer(serializers.Serializer):
    chunk_id = serializers.IntegerField()
    document_id = serializers.IntegerField()
    title = serializers.CharField()
    chunk_index = serializers.IntegerField()
    score = serializers.FloatField(help_text="Fusion (RRF) score.")
    rerank_score = serializers.FloatField(required=False, help_text="Cross-encoder score, present when reranking is on.")
    content = serializers.CharField()
