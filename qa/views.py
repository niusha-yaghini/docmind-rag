import logging

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.services.embeddings import ConfigurationError
from qa.models import QueryLog
from qa.retriever import HybridRetriever
from qa.serializers import AskSerializer, QueryLogSerializer, SearchHitSerializer, SearchParamsSerializer
from qa.services import answer_question

logger = logging.getLogger(__name__)


class AskView(APIView):
    @extend_schema(request=AskSerializer, responses={201: QueryLogSerializer}, summary="Ask a question about the documents")
    def post(self, request) -> Response:
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            log = answer_question(serializer.validated_data["question"])
        except ConfigurationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            logger.exception("Question answering failed")
            return Response(
                {"detail": "The language model or embedding service failed. Try again in a moment."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(QueryLogSerializer(log).data, status=status.HTTP_201_CREATED)


class SearchView(APIView):
    @extend_schema(
        parameters=[SearchParamsSerializer],
        responses=SearchHitSerializer(many=True),
        summary="Retrieve the most relevant chunks (no LLM call)",
    )
    def get(self, request) -> Response:
        params = SearchParamsSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        retriever = HybridRetriever()
        if "k" in params.validated_data:
            retriever.k = params.validated_data["k"]
        try:
            docs = retriever.invoke(params.validated_data["q"])
        except ConfigurationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            logger.exception("Search failed")
            return Response({"detail": "The embedding service failed. Try again in a moment."}, status=status.HTTP_502_BAD_GATEWAY)
        hits = [{**d.metadata, "content": d.page_content} for d in docs]
        return Response(SearchHitSerializer(hits, many=True).data)


class HistoryViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    """Question/answer history, newest first."""

    queryset = QueryLog.objects.all()
    serializer_class = QueryLogSerializer
