import json
import logging

from django.http import StreamingHttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.services.embeddings import ConfigurationError
from qa.models import QueryLog
from qa.retriever import HybridRetriever
from qa.serializers import AskSerializer, QueryLogSerializer, SearchHitSerializer, SearchParamsSerializer
from qa.services import answer_question, stream_answer

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


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


class IgnoreAcceptNegotiation(DefaultContentNegotiation):
    """Always answer with the first renderer (JSON for errors). A streaming client legitimately sends
    `Accept: text/event-stream`, which DRF would otherwise reject with 406 because no renderer matches it."""

    def select_renderer(self, request, renderers, format_suffix=None):
        return renderers[0], renderers[0].media_type


class AskStreamView(APIView):
    renderer_classes = [JSONRenderer]
    content_negotiation_class = IgnoreAcceptNegotiation

    @extend_schema(
        request=AskSerializer,
        responses={(200, "text/event-stream"): str},
        summary="Ask a question and stream the answer (Server-Sent Events)",
        description=(
            "Events: `token` {text} for each piece of the answer, then `done` with the stored history entry "
            "(same body as `/api/ask/`). If generation fails midway an `error` event {detail} is sent instead."
        ),
    )
    def post(self, request):
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            events = stream_answer(serializer.validated_data["question"])  # retrieval happens here
        except ConfigurationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            logger.exception("Streaming setup failed")
            return Response(
                {"detail": "The language model or embedding service failed. Try again in a moment."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        def body():
            try:
                for kind, payload in events:
                    if kind == "token":
                        yield _sse("token", {"text": payload})
                    else:
                        yield _sse("done", QueryLogSerializer(payload).data)
            except Exception:
                logger.exception("Streaming generation failed")
                yield _sse("error", {"detail": "The language model failed while answering. Try again."})

        response = StreamingHttpResponse(body(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"  # tell nginx-style proxies not to buffer the stream
        return response


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
