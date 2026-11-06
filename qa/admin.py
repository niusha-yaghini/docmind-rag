from django.contrib import admin

from qa.models import QueryLog


@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ("short_question", "model", "latency_ms", "created_at")
    list_filter = ("model", "created_at")
    search_fields = ("question", "answer")
    readonly_fields = ("question", "answer", "sources", "model", "latency_ms", "created_at")

    @admin.display(description="Question")
    def short_question(self, obj: QueryLog) -> str:
        return obj.question[:80]

    def has_add_permission(self, request) -> bool:
        return False
